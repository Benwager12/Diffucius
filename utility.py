import dataclasses
import functools
import json

import webuiapi

with open("config.json", "r") as f:
    config = json.load(f)


@dataclasses.dataclass
class _Defaults:
    cfg_scale: float = 5.0
    width: int = 512
    height: int = 512
    seed: int = -1
    show: bool = True
    steps: int = 20
    batch: int = 1
    sampler: str = "Euler a"
    save_image: bool = True
    grid: bool = True
    hires_fix: bool = False


defaults = _Defaults()


with open("defaults.json", "r+") as f:
    file_data = f.read()

    if not file_data:  # File is empty
        file_data = json.dumps(dataclasses.asdict(defaults), indent=4)
        f.write(file_data)

    file_json = json.loads(file_data)
    defaults = _Defaults(**file_json)


sd_auth: dict = config.get("sd_auth")

api = webuiapi.WebUIApi(
    host=sd_auth.get("host"),
    port=sd_auth.get("port"),
    use_https=sd_auth.get("use_https", False)
)

if sd_auth.get("username") and sd_auth.get("password"):
    api.set_auth(sd_auth.get("username"), sd_auth.get("password"))


@functools.lru_cache
def get_models():
    return [model.get("model_name") for model in api.get_sd_models()]


@functools.lru_cache
def model_with_hash():
    return [(model.get("model_name"), model.get("title")) for model in api.get_sd_models()]


@functools.lru_cache(maxsize=16)
def model_name_to_hash_name(model_name):
    for model in model_with_hash():
        if model[0] == model_name:
            return model[1]

    return None


@functools.lru_cache(maxsize=16)
def hash_name_to_model_name(hash_name):
    for model in model_with_hash():
        if model[1] == hash_name:
            return model[0]

    return None


def get_model():
    checkpoint = api.get_options().get("sd_model_checkpoint")
    return hash_name_to_model_name(checkpoint)


def get_sampler_names():
    return [sampler.get("name") for sampler in api.get_samplers()]
