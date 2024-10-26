import os, sys, pdb, torch
import warnings
import subprocess
from datetime import datetime

# Handle PyInstaller paths
def resource_path(relative_path):
    """Get path to resource relative to the executable's location."""
    # Get the directory of the executable if frozen (PyInstaller), else use script location
    base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

now_dir = os.getcwd()
sys.path.append(now_dir)
tmp = os.path.join(now_dir, "TEMP")
os.environ["TEMP"] = tmp
warnings.filterwarnings("ignore")
torch.manual_seed(114514)

import argparse
import glob
import torch
import numpy as np
import yaml
import pkg_resources

from multiprocessing import cpu_count
import sys
import os

# Add the parent directory to sys.path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

from Utilities.vc_infer_pipeline import VC
from Utilities.Pack.models import (
    SynthesizerTrnMs256NSFsid,
    SynthesizerTrnMs256NSFsid_nono,
)
from Utilities.Pack.modelsv2 import (
    SynthesizerTrnMs768NSFsid_nono,
    SynthesizerTrnMs768NSFsid,
)
from Utilities.audio import load_audio

from fairseq import checkpoint_utils
from scipy.io import wavfile
from dotenv import load_dotenv

load_dotenv()

AUDIO_INPUT = resource_path("../Assets/Audio")
MODEL_INPUT = resource_path("../Utilities/Models/Hana.V5.pth")
INDEX_INPUT =  resource_path("../Utilities/Models/added_IVF495_Flat_nprobe_1_Hana.V5_v2.V2_v2.index")

class Config:
    def __init__(self, device, is_half):
        self.device = device
        self.is_half = is_half
        self.n_cpu = 0
        self.gpu_name = None
        self.gpu_mem = None
        self.x_pad, self.x_query, self.x_center, self.x_max = self.device_config()

    def device_config(self) -> tuple:
        if torch.cuda.is_available():
            i_device = int(self.device.split(":")[-1])
            self.gpu_name = torch.cuda.get_device_name(i_device)
            if (
                ("16" in self.gpu_name and "V100" not in self.gpu_name.upper())
                or "P40" in self.gpu_name.upper()
                or "1060" in self.gpu_name
                or "1070" in self.gpu_name
                or "1080" in self.gpu_name
            ):
                print("16系/10系显卡和P40强制单精度")
                self.is_half = False
                for config_file in ["32k.json", "40k.json", "48k.json"]:
                    with open(f"configs/{config_file}", "r") as f:
                        strr = f.read().replace("true", "false")
                    with open(f"configs/{config_file}", "w") as f:
                        f.write(strr)
                with open("trainset_preprocess_pipeline_print.py", "r") as f:
                    strr = f.read().replace("3.7", "3.0")
                with open("trainset_preprocess_pipeline_print.py", "w") as f:
                    f.write(strr)
            else:
                self.gpu_name = None
            self.gpu_mem = int(
                torch.cuda.get_device_properties(i_device).total_memory
                / 1024
                / 1024
                / 1024
                + 0.4
            )
            if self.gpu_mem <= 4:
                with open("trainset_preprocess_pipeline_print.py", "r") as f:
                    strr = f.read().replace("3.7", "3.0")
                with open("trainset_preprocess_pipeline_print.py", "w") as f:
                    f.write(strr)
        elif torch.backends.mps.is_available():
            print("没有发现支持的N卡, 使用MPS进行推理")
            self.device = "mps"
        else:
            print("没有发现支持的N卡, 使用CPU进行推理")
            self.device = "cpu"
            self.is_half = True

        if self.n_cpu == 0:
            self.n_cpu = cpu_count()

        if self.is_half:
            # 6G显存配置
            x_pad = 3
            x_query = 10
            x_center = 60
            x_max = 65
        else:
            # 5G显存配置
            x_pad = 1
            x_query = 6
            x_center = 38
            x_max = 41

        if self.gpu_mem != None and self.gpu_mem <= 4:
            x_pad = 1
            x_query = 5
            x_center = 30
            x_max = 32

        return x_pad, x_query, x_center, x_max


def get_path(name):
    """
    Built to get the path of a file based on where the initial script is being run from.

    Args:
        - name(str) : name of the file/folder
    """
    return os.path.join(os.getcwd(), name)


def create_directory(name):
    """
    Creates a directory based on the location from which the script is run. Relies on
    get_path()

    Args:
        - name(str) : name of the file/folder
    """
    dir_name = get_path(name)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def load_hubert(file_path=None):
    """
    Args:
        file_fath (str) : Direct path location to the hubert_base.  If not specified, defaults to top level directory.
    """
    global hubert_model
    if file_path is None:
        file_path = resource_path("../Utilities/Models/hubert_base.pt")
    models, _, _ = checkpoint_utils.load_model_ensemble_and_task(
        [file_path],
        suffix="",
    )
    hubert_model = models[0]
    hubert_model = hubert_model.to(config.device)
    if config.is_half:
        hubert_model = hubert_model.half()
    else:
        hubert_model = hubert_model.float()
    hubert_model.eval()


def vc_single(
    sid,
    input_audio_path,
    f0_up_key,
    f0_file,
    f0_method,
    file_index,
    file_index2,
    # file_big_npy,
    index_rate,
    filter_radius,
    resample_sr,
    rms_mix_rate,
    protect,
):  # spk_item, input_audio0, vc_transform0,f0_file,f0method0
    global tgt_sr, net_g, vc, hubert_model, version
    f0_file = None
    if input_audio_path is None:
        return "You need to upload an audio", None
    f0_up_key = int(f0_up_key)
    audio = load_audio(input_audio_path, 16000)
    audio_max = np.abs(audio).max() / 0.95
    if audio_max > 1:
        audio /= audio_max
    times = [0, 0, 0]
    if not hubert_model:
        load_hubert()
    if_f0 = cpt.get("f0", 1)
    file_index = (
        (
            file_index.strip(" ")
            .strip('"')
            .strip("\n")
            .strip('"')
            .strip(" ")
            .replace("trained", "added")
        )
        if file_index != ""
        else file_index2
    )  # 防止小白写错，自动帮他替换掉
    # file_big_npy = (
    #     file_big_npy.strip(" ").strip('"').strip("\n").strip('"').strip(" ")
    # )
    audio_opt = vc.pipeline(
        hubert_model,
        net_g,
        sid,
        audio,
        times,
        f0_up_key,
        f0_method,
        file_index,
        # file_big_npy,
        index_rate,
        if_f0,
        version,
        protect,
        f0_file=f0_file,
    )
    return audio_opt


def get_vc(model_path):
    global n_spk, tgt_sr, net_g, vc, cpt, device, is_half, version
    print("loading pth %s" % model_path)
    cpt = torch.load(model_path, map_location="cpu")
    tgt_sr = cpt["config"][-1]
    cpt["config"][-3] = cpt["weight"]["emb_g.weight"].shape[0]  # n_spk
    if_f0 = cpt.get("f0", 1)
    version = cpt.get("version", "v1")
    if version == "v1":
        if if_f0 == 1:
            net_g = SynthesizerTrnMs256NSFsid(*cpt["config"], is_half=config.is_half)
        else:
            net_g = SynthesizerTrnMs256NSFsid_nono(*cpt["config"])
    elif version == "v2":
        if if_f0 == 1:
            net_g = SynthesizerTrnMs768NSFsid(*cpt["config"], is_half=config.is_half)
        else:
            net_g = SynthesizerTrnMs768NSFsid_nono(*cpt["config"])
    del net_g.enc_q
    print(net_g.load_state_dict(cpt["weight"], strict=False))
    net_g.eval().to(device)
    if is_half:
        net_g = net_g.half()
    else:
        net_g = net_g.float()
    vc = VC(tgt_sr, config)
    n_spk = cpt["config"][-3]
    # return {"visible": True,"maximum": n_spk, "__type__": "update"}


def load_config():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_file = os.path.join(current_dir, "rvc.yaml")

    with open(yaml_file, "r") as file:
        rvc_conf = yaml.safe_load(file)

    return rvc_conf


def rvc_convert(
    model_path,
    output_file,
    f0_up_key=5,
    input_path=None,
    output_dir_path=None,
    _is_half="False",
    f0method="harvest",
    file_index=INDEX_INPUT,
    file_index2="",
    index_rate=1,
    filter_radius=3,
    resample_sr=0,
    rms_mix_rate=0.2,
    protect=1,
):
    """
    Function to call for the rvc voice conversion.  All parameters are the same present in that of the webui

    Args:
        model_path (str) : path to the rvc voice model you're using
        f0_up_key (int) : transpose of the audio file, changes pitch (positive makes voice higher pitch)
        input_path (str) : path to audio file (use wav file)
        output_dir_path (str) : path to output directory, defaults to parent directory in output folder
        _is_half (str) : Determines half-precision
        f0method (str) : picks which f0 method to use: dio, harvest, crepe, rmvpe (requires rmvpe.pt)
        file_index (str) : path to file_index, defaults to None
        file_index2 (str) : path to file_index2, defaults to None.  #honestly don't know what this is for
        index_rate (int) : strength of the index file if provided
        filter_radius (int) : if >=3: apply median filtering to the harvested pitch results. The value represents the filter radius and can reduce breathiness.
        resample_sr (int) : quality at which to resample audio to, defaults to no resample
        rmx_mix_rate (int) : adjust the volume envelope scaling. Closer to 0, the more it mimicks the volume of the original vocals. Can help mask noise and make volume sound more natural when set relatively low. Closer to 1 will be more of a consistently loud volume
        protect (int) : protect voiceless consonants and breath sounds to prevent artifacts such as tearing in electronic music. Set to 0.5 to disable. Decrease the value to increase protection, but it may reduce indexing accuracy

    Returns:
        output_file_path (str) : file path and name of tshe output wav file

    """
    global config, now_dir, hubert_model, tgt_sr, net_g, vc, cpt, device, is_half, version

    if torch.cuda.is_available():
        device = "cuda:0"
    elif torch.backends.mps.is_available():
        device = "mps:0"
    else:
        print("Cuda or MPS not detected")

    is_half = _is_half

    # Left over from manual yaml usage, DELETE in the future
    # settings = load_config()

    # f0_up_key = settings["transpose"]
    # input_path = settings["audio_file"]
    # # output_dir = settings["output_dir"]
    # model_path = get_path(settings["model_path"])
    # device = settings["device"]
    # is_half = settings["is_half"]
    # f0method = settings["f0method"]
    # file_index = settings["file_index"]
    # file_index2 = settings["file_index2"]
    # index_rate = settings["index_rate"]
    # filter_radius = settings["filter_radius"]
    # resample_sr = settings["resample_sr"]
    # rms_mix_rate = settings["rms_mix_rate"]
    # protect = settings["protect"]
    # print(settings)
    print(f"{type(output_file)}")
    if output_dir_path == None:
        output_dir_path = AUDIO_INPUT
        output_file = output_file
        output_dir = os.getcwd()
        output_file_path = os.path.join(output_dir, output_dir_path, output_file)
    else:
        # Mainly for Jarod's Vivy project, specify entire path + wav name
        output_file_path = output_dir_path
        pass

    create_directory(output_dir_path)
    output_dir = get_path(output_dir_path)

    if is_half.lower() == "true":
        is_half = True
    else:
        is_half = False

    config = Config(device, is_half)
    now_dir = os.getcwd()
    sys.path.append(now_dir)

    hubert_model = None

    get_vc(model_path)
    wav_opt = vc_single(
        0,
        input_path,
        f0_up_key,
        None,
        f0method,
        file_index,
        file_index2,
        index_rate,
        filter_radius,
        resample_sr,
        rms_mix_rate,
        protect,
    )
    wavfile.write(output_file_path, tgt_sr, wav_opt)

    return output_file_path

def log_debug(message, width=150):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Prepare the log prefix (timestamp + INFO label)
        prefix = f"{timestamp} | INFO | "
        
        # Calculate the available width for the message (subtract prefix length from total width)
        available_width = width - len(prefix)

        # If the message is too long, truncate it and add ...{hidden}
        if len(message) > available_width:
            message = message[:available_width - len("...{скрытый}")] + "...{скрытый}"

        # Print the final log message with the prefix
        print(f"{prefix}{message}")


def mainrvc(input, output_path):

    # Split the output_path into directory and file name
    output_dir = os.path.dirname(output_path)
    output_file_name = os.path.basename(output_path)

    log_debug(f"{output_path}")  # Correctly referencing the passed argument
    # Need to comment out yaml setting for input audio
    rvc_convert(
        model_path=MODEL_INPUT,
        input_path=input,
        output_file=output_file_name
    )


if __name__ == "__main__":
    input = resource_path("../Assets/Audio/ai.wav")
    output = resource_path("../Assets/Audio/hana.wav")
    mainrvc(input, output)
