# -*- coding: UTF-8 -*-
import os
import datetime
import requests
from loguru import logger
from pathlib import Path


def download(url_path):
    req = requests.get(url_path)
    filename = url_path.split('/')[-1]
    if req.status_code != 200:
        print('文件下载异常')
        return False
    base_path = Path(__file__).parent.parent
    img_path = base_path.joinpath('./img').resolve()  # 获得文件夹的绝对路径
    if not img_path.exists():  # 日志文件夹不存在就新建
        img_path.mkdir()
    file_path = f"{img_path}/{datetime.datetime.now().strftime('%Y%m%d')}_{filename}"
    try:
        with open(file_path, 'wb') as f:
            f.write(req.content)
            f.close()
    except Exception as e:
        print(e)
    return file_path


# 基于PicFast 服务的图片上传
class PFService:
    def __init__(self, app_key, app_secret, endpoint):
        """

        :param app_key:
        :param app_secret:
        :param endpoint:
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.endpoint = endpoint

    def get_token(self):
        """
        获取token
        :return:
        """
        url = f"{self.endpoint}/api/v1/auth/token"
        data = {
            "x_access_key": self.app_key,
            "x_secret_key": self.app_secret
        }
        res = requests.post(url, json=data)
        if res.status_code != 200:
            print("token 获取失败:", res.status_code)
            return False
        return res.json()['data']['access_token']

    def get_file_key(self, file_path):
        """
        Upload an image to the server

        Args:
            file_path: Path to the image file

        Returns:
            Response from the server
        """
        url = f"{self.endpoint}/api/v1/image/upload"
        headers = {
            "Authorization": f"Bearer {self.get_token()}",
            "X-Token-Type": "access"
        }

        with open(file_path, 'rb') as f:
            files = {'file': (file_path.split('/')[-1], f, 'application/octet-stream')}
            response = requests.post(url, headers=headers, files=files)
        if response.status_code != 200:
            print("image <UNK>:", response.status_code)
            return False
        return response.json()['data']['file_key']

    def setup(self, file_path):
        """
        同步方式上传文件
        :param file_path: UploadFileDto 对象
        :return:
        """
        file_key = self.get_file_key(file_path)
        file_url = self.get_full_url(file_key)
        return file_key, file_url

    def get_full_url(self, file_key):
        """
        返回图片的网络路径
        :param file_key:
        :return:
        """

        return self.endpoint + "/api/v1/image/" + file_key


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("调用错误, 图片格式不对")
        sys.exit(1)
    end_point = "http://127.0.0.1:8099"

    x_access_key = "ak-xxx"
    x_secret_key = "sk-xxx"
    pf_service = PFService(x_access_key, x_secret_key, end_point)
    # python /PicFast/docs/typora/picgo.py
    # 节点名称
    url_list = []
    for i in range(1, len(sys.argv)):
        path = sys.argv[i]
        if path.startswith("http"):
            path = download(path)
        logger.info(path)
        name, url = pf_service.setup(path)
        url_list.append(url)
        try:
            os.remove(path)
        except:
            pass

    print("Upload Success:")
    for url in url_list:
        print(url)
