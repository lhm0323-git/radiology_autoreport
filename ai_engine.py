import cv2
import numpy as np
import os
import torch
import sys
from types import ModuleType

class MockAlbumentations(ModuleType):
    def Resize(self, height, width, p=1):
        def wrapper(image):
            image = cv2.resize(image, (width, height))
            return {"image": image}
        return wrapper

    def LongestMaxSize(self, max_size, p):
        def wrapper(image):
            h, w = image.shape[:2]
            scale = max_size / max(h, w)
            if scale != 1.0:
                image = cv2.resize(image, (int(w*scale), int(h*scale)))
            return {"image": image}
        return wrapper

    def PadIfNeeded(self, min_height, min_width, border_mode, p):
        def wrapper(image):
            h, w = image.shape[:2]
            pad_h = max(0, min_height - h)
            pad_w = max(0, min_width - w)
            if pad_h > 0 or pad_w > 0:
                top = pad_h // 2
                bottom = pad_h - top
                left = pad_w // 2
                right = pad_w - left
                image = cv2.copyMakeBorder(image, top, bottom, left, right, border_mode)
            return {"image": image}
        return wrapper

sys.modules['albumentations'] = MockAlbumentations('albumentations')

from skimage.exposure import match_histograms
from transformers import AutoModel, PreTrainedModel
if not hasattr(PreTrainedModel, 'all_tied_weights_keys'):
    PreTrainedModel.all_tied_weights_keys = property(lambda self: {})

class BoneAgeAIEngine:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Initializing AI Engine on {self.device}...")
        
        try:
            # Load Crop Model from local cache only for deterministic offline deployment.
            self.crop_model = AutoModel.from_pretrained(
                "ianpan/bone-age-crop",
                trust_remote_code=True,
                local_files_only=True,
            )
            self.crop_model = self.crop_model.eval().to(self.device)

            # Load Main Model from local cache only for deterministic offline deployment.
            self.main_model = AutoModel.from_pretrained(
                "ianpan/bone-age",
                trust_remote_code=True,
                local_files_only=True,
            )
            self.main_model = self.main_model.eval().to(self.device)
        except Exception as e:
            print("AI model files were not found in the local HuggingFace cache.")
            print("Run preload_models.py once in a network-enabled environment, then retry offline.")
            raise e
        
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        self.ref_img_path = os.path.join(application_path, "ref_img.png")
        if not os.path.exists(self.ref_img_path):
            print(f"Warning: Reference image not found at {self.ref_img_path}")

    def predict(self, image, is_female):
        try:
            # 1. Convert to grayscale if not already
            if len(image.shape) == 3:
                img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                img = image
                
            img_shape = torch.tensor([img.shape[:2]])
            
            # 2. Crop
            x_crop = self.crop_model.preprocess(img)
            x_crop = torch.from_numpy(x_crop).unsqueeze(0).unsqueeze(0).float()
            
            with torch.inference_mode():
                coords = self.crop_model(x_crop.to(self.device), img_shape.to(self.device))
                
            coords = coords[0].cpu().numpy()
            x, y, w, h = coords
            
            # coords are float, need to round and convert to int
            x, y, w, h = int(x), int(y), int(w), int(h)
            
            # Ensure coordinates are within image bounds
            y = max(0, y)
            x = max(0, x)
            h = min(h, img.shape[0] - y)
            w = min(w, img.shape[1] - x)
            
            cropped_img = img[y: y + h, x: x + w]
            
            # 3. Histogram Matching
            if os.path.exists(self.ref_img_path):
                ref = cv2.imread(self.ref_img_path, 0)
                cropped_img = match_histograms(cropped_img, ref)
            
            # 4. Main Inference
            x_main = self.main_model.preprocess(cropped_img)
            x_main = torch.from_numpy(x_main).unsqueeze(0).unsqueeze(0).float()
            
            female_tensor = torch.tensor([1 if is_female else 0])
            
            with torch.inference_mode():
                bone_age = self.main_model(x_main.to(self.device), female_tensor.to(self.device))
                
            predicted_months = bone_age.item()
            return predicted_months
            
        except Exception as e:
            print(f"AI Engine Error: {e}")
            raise e
