import csv
from functools import lru_cache
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F
from PIL import Image
from torch import nn
from torchvision import transforms

OUTPUT_DIM = 65
MODEL_NAME = "siglip2"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BASE_DIR = Path(__file__).resolve().parent
WEIGHTS_PATH = BASE_DIR / "weights" / "siglip2_66epoch.pth"
CLASS_MAP_PATH = BASE_DIR.parent / "src" / "assets" / "class_map.csv"
IMAGE_SIZE = 224
PATCH_SIZE = 16
HIDDEN_SIZE = 768
INTERMEDIATE_SIZE = 3072
NUM_HEADS = 12
NUM_LAYERS = 12
IMAGE_TRANSFORM = transforms.Compose(
    [
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)
CLASS_NAMES = [f"class_{index}" for index in range(OUTPUT_DIM)]


def _humanize_class_name(class_name: str) -> str:
    return class_name.replace("___", " - ").replace("_", " ")


@lru_cache(maxsize=1)
def _load_class_names() -> list[str]:
    class_names = CLASS_NAMES.copy()

    if not CLASS_MAP_PATH.exists():
        return class_names

    with CLASS_MAP_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            label = row.get("label")
            class_name = row.get("class_name")

            if label is None or class_name is None:
                continue

            try:
                class_index = int(label)
            except ValueError:
                continue

            if 0 <= class_index < len(class_names):
                class_names[class_index] = class_name

    return class_names


class SiglipEmbeddings(nn.Module):
    def __init__(
        self,
        image_size: int = IMAGE_SIZE,
        patch_size: int = PATCH_SIZE,
        hidden_size: int = HIDDEN_SIZE,
    ):
        super().__init__()
        self.patch_embedding = nn.Conv2d(
            in_channels=3,
            out_channels=hidden_size,
            kernel_size=patch_size,
            stride=patch_size,
            bias=True,
        )
        self.num_patches = (image_size // patch_size) ** 2
        self.position_embedding = nn.Embedding(self.num_patches, hidden_size)

    def forward(self, pixel_values: torch.Tensor) -> torch.Tensor:
        embeddings = self.patch_embedding(pixel_values)
        embeddings = embeddings.flatten(2).transpose(1, 2)
        position_ids = torch.arange(self.num_patches, device=embeddings.device)
        position_embeddings = self.position_embedding(position_ids).unsqueeze(0)
        return embeddings + position_embeddings


class SiglipSelfAttention(nn.Module):
    def __init__(self, hidden_size: int = HIDDEN_SIZE, num_heads: int = NUM_HEADS):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads

        self.k_proj = nn.Linear(hidden_size, hidden_size)
        self.v_proj = nn.Linear(hidden_size, hidden_size)
        self.q_proj = nn.Linear(hidden_size, hidden_size)
        self.out_proj = nn.Linear(hidden_size, hidden_size)

    def _shape(self, tensor: torch.Tensor, batch_size: int, sequence_length: int) -> torch.Tensor:
        return tensor.view(batch_size, sequence_length, self.num_heads, self.head_dim).transpose(1, 2)

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        batch_size, sequence_length, _ = hidden_states.shape

        query_states = self._shape(self.q_proj(hidden_states), batch_size, sequence_length)
        key_states = self._shape(self.k_proj(hidden_states), batch_size, sequence_length)
        value_states = self._shape(self.v_proj(hidden_states), batch_size, sequence_length)

        attention_scores = torch.matmul(query_states, key_states.transpose(-1, -2))
        attention_scores = attention_scores / (self.head_dim**0.5)
        attention_probs = F.softmax(attention_scores, dim=-1)

        context_states = torch.matmul(attention_probs, value_states)
        context_states = context_states.transpose(1, 2).contiguous()
        context_states = context_states.view(batch_size, sequence_length, self.hidden_size)
        return self.out_proj(context_states)


class SiglipMLP(nn.Module):
    def __init__(self, hidden_size: int = HIDDEN_SIZE, intermediate_size: int = INTERMEDIATE_SIZE):
        super().__init__()
        self.fc1 = nn.Linear(hidden_size, intermediate_size)
        self.fc2 = nn.Linear(intermediate_size, hidden_size)

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        hidden_states = self.fc1(hidden_states)
        hidden_states = F.gelu(hidden_states)
        return self.fc2(hidden_states)


class SiglipEncoderLayer(nn.Module):
    def __init__(self):
        super().__init__()
        self.layer_norm1 = nn.LayerNorm(HIDDEN_SIZE)
        self.self_attn = SiglipSelfAttention(HIDDEN_SIZE, NUM_HEADS)
        self.layer_norm2 = nn.LayerNorm(HIDDEN_SIZE)
        self.mlp = SiglipMLP(HIDDEN_SIZE, INTERMEDIATE_SIZE)

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        hidden_states = hidden_states + self.self_attn(self.layer_norm1(hidden_states))
        hidden_states = hidden_states + self.mlp(self.layer_norm2(hidden_states))
        return hidden_states


class SiglipEncoder(nn.Module):
    def __init__(self, num_layers: int = NUM_LAYERS):
        super().__init__()
        self.layers = nn.ModuleList(SiglipEncoderLayer() for _ in range(num_layers))

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        for layer in self.layers:
            hidden_states = layer(hidden_states)
        return hidden_states


class SiglipMultiheadAttentionPoolingHead(nn.Module):
    def __init__(self):
        super().__init__()
        self.probe = nn.Parameter(torch.randn(1, 1, HIDDEN_SIZE))
        self.attention = nn.MultiheadAttention(HIDDEN_SIZE, NUM_HEADS, batch_first=True)
        self.layernorm = nn.LayerNorm(HIDDEN_SIZE)
        self.mlp = SiglipMLP(HIDDEN_SIZE, INTERMEDIATE_SIZE)

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        batch_size = hidden_states.shape[0]
        probe = self.probe.expand(batch_size, -1, -1)
        pooled_output, _ = self.attention(probe, hidden_states, hidden_states, need_weights=False)
        pooled_output = pooled_output + self.mlp(self.layernorm(pooled_output))
        return pooled_output[:, 0]


class SiglipVisionTransformer(nn.Module):
    def __init__(self):
        super().__init__()
        self.embeddings = SiglipEmbeddings(IMAGE_SIZE, PATCH_SIZE, HIDDEN_SIZE)
        self.encoder = SiglipEncoder(NUM_LAYERS)
        self.post_layernorm = nn.LayerNorm(HIDDEN_SIZE)
        self.head = SiglipMultiheadAttentionPoolingHead()

    def forward(self, pixel_values: torch.Tensor) -> torch.Tensor:
        hidden_states = self.embeddings(pixel_values)
        hidden_states = self.encoder(hidden_states)
        hidden_states = self.post_layernorm(hidden_states)
        return self.head(hidden_states)


class Model(nn.Module):
    def __init__(self, model_name: str = MODEL_NAME, output_dim: int = OUTPUT_DIM):
        super().__init__()

        if model_name != MODEL_NAME:
            raise ValueError(f"Unsupported model: {model_name}")

        self.model_name = model_name
        self.model = SiglipVisionTransformer()
        self.mlp = nn.Sequential(
            nn.Dropout(p=0.4),
            nn.ReLU(),
            nn.Linear(HIDDEN_SIZE, output_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.model(x)
        x = self.mlp(x)
        return x


def _normalize_checkpoint_keys(state_dict: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    if all(key.startswith("module.") for key in state_dict):
        return {key.removeprefix("module."): value for key, value in state_dict.items()}
    return state_dict


def _extract_state_dict(checkpoint: object) -> dict[str, torch.Tensor]:
    if not isinstance(checkpoint, dict):
        raise ValueError("Expected checkpoint to contain a dictionary")

    if all(isinstance(value, torch.Tensor) for value in checkpoint.values()):
        return checkpoint  # type: ignore[return-value]

    for key in ("state_dict", "model_state_dict", "model"):
        value = checkpoint.get(key)
        if isinstance(value, dict) and all(isinstance(tensor, torch.Tensor) for tensor in value.values()):
            return value  # type: ignore[return-value]

    raise ValueError("Could not find a valid state_dict in checkpoint")


@lru_cache(maxsize=1)
def load_model() -> Model:
    if not WEIGHTS_PATH.exists():
        raise FileNotFoundError(f"Model weights not found at {WEIGHTS_PATH}")

    model = Model().to(DEVICE)
    checkpoint = torch.load(WEIGHTS_PATH, map_location=DEVICE)

    state_dict = _normalize_checkpoint_keys(_extract_state_dict(checkpoint))
    model.load_state_dict(state_dict, strict=True)
    model.eval()
    return model


def predict_image(image: Image.Image) -> dict[str, Any]:
    model = load_model()
    mapped_class_names = _load_class_names()
    image_tensor = IMAGE_TRANSFORM(image.convert("RGB")).unsqueeze(0).to(DEVICE)

    with torch.inference_mode():
        logits = model(image_tensor)
        probabilities = torch.softmax(logits, dim=1)
        confidence, predicted_index = torch.max(probabilities, dim=1)

    class_index = int(predicted_index.item())
    raw_class_name = mapped_class_names[class_index]
    readable_name = _humanize_class_name(raw_class_name)
    print(f"Predicted class: {raw_class_name}, Confidence: {confidence.item():.4f}")
    return {
        "disease": readable_name,
        "class_name": raw_class_name,
        "class_index": class_index,
        "confidence": float(confidence.item()),
        "description": readable_name,
    }
