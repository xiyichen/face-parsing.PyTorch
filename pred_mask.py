#!/usr/bin/python
# -*- encoding: utf-8 -*-

from logger import setup_logger
from model import BiSeNet

import torch

import os
import os.path as osp
import numpy as np
from PIL import Image
import torchvision.transforms as transforms
import cv2

def vis_parsing_maps(im, parsing_anno, stride, save_im=False, save_path='vis_results/parsing_map_on_im.jpg'):
    # Colors for all 20 parts
    part_colors = [[255, 0, 0], [255, 85, 0], [255, 170, 0],
                   [255, 0, 85], [255, 0, 170],
                   [0, 255, 0], [85, 255, 0], [170, 255, 0],
                   [0, 255, 85], [0, 255, 170],
                   [0, 0, 255], [85, 0, 255], [170, 0, 255],
                   [0, 85, 255], [0, 170, 255],
                   [255, 255, 0], [255, 255, 85], [255, 255, 170],
                   [255, 0, 255], [255, 85, 255], [255, 170, 255],
                   [0, 255, 255], [85, 255, 255], [170, 255, 255]]

    im = np.array(im)
    vis_im = im.copy().astype(np.uint8)
    vis_parsing_anno = parsing_anno.copy().astype(np.uint8)
    vis_parsing_anno = cv2.resize(vis_parsing_anno, None, fx=stride, fy=stride, interpolation=cv2.INTER_NEAREST)
    vis_parsing_anno_color = np.zeros((vis_parsing_anno.shape[0], vis_parsing_anno.shape[1], 3)) + 255

    num_of_class = np.max(vis_parsing_anno)

    for pi in range(1, num_of_class + 1):
        index = np.where(vis_parsing_anno == pi)
        vis_parsing_anno_color[index[0], index[1], :] = part_colors[pi]

    vis_parsing_anno_color = vis_parsing_anno_color.astype(np.uint8)
    # print(vis_parsing_anno_color.shape, vis_im.shape)
    vis_im = cv2.addWeighted(cv2.cvtColor(vis_im, cv2.COLOR_RGB2BGR), 0.4, vis_parsing_anno_color, 0.6, 0)

    # Save result or not
    if save_im:
        # cv2.imwrite(save_path[:-4] +'.png', vis_parsing_anno)
        cv2.imwrite(save_path, vis_im, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

    # return vis_im

def evaluate(respth='./res/test_res', dspth='./data', model_path='model_final_diss.pth', save_masks=True, save_imgs=True):

    if not os.path.exists(respth):
        os.makedirs(respth)

    mask_path = osp.join(respth, 'masks')

    if not os.path.exists(mask_path):
        os.makedirs(osp.join(mask_path))

    n_classes = 19
    net = BiSeNet(n_classes=n_classes)
    if torch.cuda.is_available():
        net.cuda()
    if torch.cuda.is_available():
        net.load_state_dict(torch.load(model_path))
    else:
        net.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    net.eval()

    to_tensor = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
    ])
    masks_all = []
    with torch.no_grad():
        for image_path in os.listdir(dspth):
            print(image_path)
            img = Image.open(osp.join(dspth, image_path))
            img_orig = img.copy()
            W, H = img.size
            image = img.resize((512, 512), Image.BILINEAR)
            img = to_tensor(image)
            img = torch.unsqueeze(img, 0)
            if torch.cuda.is_available():
                img = img.cuda()
            out = net(img)[0]
            parsing = out.squeeze(0).cpu().numpy().argmax(0)
            for i in range(len(parsing)):
                for j in range(len(parsing[i])):
                    if parsing[i][j] in [1,2,3,4,5,6,10,11,12,13]:
                        parsing[i][j] = 1
                    else:
                        parsing[i][j] = 0
            parsing_im = Image.fromarray((parsing * 255).astype(np.uint8))
            parsing_im = parsing_im.resize((W, H), Image.BILINEAR)
            parsing = np.array(parsing_im)
            parsing = (parsing / 255).astype(np.float64)
            parsing[parsing>=0.5] = 1
            parsing[parsing<0.5] = 0
            if save_masks:
                np.save(osp.join(mask_path, image_path[:-4]), parsing)
            masks_all.append(parsing)

            if save_imgs:
                vis_parsing_maps(img_orig, parsing, stride=1, save_im=True, save_path=osp.join(respth, image_path))

    return masks_all






if __name__ == "__main__":
    evaluate(dspth='/Users/xiyichen/Documents/3d_vision/Learning-to-Reconstruct-3D-Faces-by-Watching-TV/id_1', model_path='/Users/xiyichen/Documents/3d_vision/Learning-to-Reconstruct-3D-Faces-by-Watching-TV/face-parsing.PyTorch/res/cp/79999_iter.pth')

