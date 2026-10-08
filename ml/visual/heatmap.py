"""
Grad-CAM Heatmap and Visual Attribution Generator for PyTorch Forensics Detectors.
Extracts gradient-weighted activation maps to highlight artifact regions.
"""
from typing import Tuple
import cv2
import numpy as np
import torch
import torch.nn.functional as F

from ml.visual.efficientnet_detector import EfficientNetDetector


class GradCAMExplainer:
    def __init__(self, detector: EfficientNetDetector):
        self.detector = detector
        self.model = detector.model
        self.device = detector.device
        self.gradients = None
        self.activations = None
        
        # Register hooks onto the final convolutional layer of EfficientNet-B0
        target_layer = self.model.features[-1]
        
        target_layer.register_forward_hook(self._forward_hook)
        target_layer.register_full_backward_hook(self._backward_hook)

    def _forward_hook(self, module, input, output):
        self.activations = output

    def _backward_hook(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]

    def generate_heatmap(
        self, face_bgr: np.ndarray, target_class: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes Grad-CAM heatmap and blended overlay for a given face crop.
        Returns:
            heatmap_colormap: (H, W, 3) BGR colormap of normalized activation weights.
            overlay: (H, W, 3) BGR blended original face + colormap.
        """
        if face_bgr is None or face_bgr.size == 0:
            blank = np.zeros((224, 224, 3), dtype=np.uint8)
            return blank, blank

        h_orig, w_orig = face_bgr.shape[:2]
        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        tensor = self.detector.transform(face_rgb).unsqueeze(0).to(self.device)
        tensor.requires_grad = True

        self.model.zero_grad()
        logits = self.model(tensor)
        
        # Target score (Manipulated class = 1)
        score = logits[0, target_class]
        score.backward(retain_graph=True)

        if self.gradients is None or self.activations is None:
            blank = np.zeros((h_orig, w_orig, 3), dtype=np.uint8)
            return blank, blank

        # Global average pooling of gradients
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
        
        # Weighted combination of forward activation maps
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True)
        cam = F.relu(cam)
        cam_np = cam.detach().cpu().squeeze().numpy()

        # Normalize between 0 and 1
        cam_max = np.max(cam_np)
        if cam_max > 0:
            cam_norm = cam_np / cam_max
        else:
            cam_norm = cam_np

        # Resize to original face crop dimensions
        cam_resized = cv2.resize(cam_norm, (w_orig, h_orig))
        heatmap_uint8 = np.uint8(255 * cam_resized)
        
        # Apply JET colormap
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

        # Blend with original face
        overlay = cv2.addWeighted(face_bgr, 0.6, heatmap_colored, 0.4, 0)

        return heatmap_colored, overlay
