import functools
import json

import webuiapi

with open("config.json", "r") as f:
    config = json.load(f)

url = "127.0.0.1"

sd_auth: dict = config.get("sd_auth")

api = webuiapi.WebUIApi(
    host=sd_auth.get("host", "127.0.0.1"),
    port=sd_auth.get("port", 7860)
)

if sd_auth.get("username") and sd_auth.get("password"):
    api.set_auth(sd_auth.get("username"), sd_auth.get("password"))


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



