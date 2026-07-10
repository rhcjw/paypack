"""
支付宝 AI 付签名器 —— 中国合规支付通道。
使用支付宝开放平台 API（JSAPI支付 / APP支付）。
"""

import os
import time
import json
import base64
from typing import Optional
from datetime import datetime
from urllib.parse import urlencode

import requests
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256

from paypack.signer.base import Signer


class AlipaySigner(Signer):
    """
    支付宝支付签名器。

    支持:
    - JSAPI 支付（小程序/网页）
    - APP 支付（移动端）
    - 交易查询
    - 退款

    前置条件:
        pip install pycryptodome requests

    Usage:
        signer = AlipaySigner(
            app_id="你的APPID",
            private_key_path="path/to/private_key.pem",
            alipay_public_key_path="path/to/alipay_public_key.pem",
        )
        pay = AgentPay(signer=signer, network="alipay")
        pay.send(to="2088xxx", amount=0.01, currency="CNY",
                 subject="AI数据订阅费", buyer_id="用户支付宝user_id")
    """

    GATEWAY_URL = "https://openapi.alipay.com/gateway.do"
    SANDBOX_URL = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"

    def __init__(
        self,
        app_id: str,
        private_key: Optional[str] = None,
        private_key_path: Optional[str] = None,
        alipay_public_key: Optional[str] = None,
        alipay_public_key_path: Optional[str] = None,
        sandbox: bool = False,
        notify_url: Optional[str] = None,
        return_url: Optional[str] = None,
    ):
        """
        Args:
            app_id: 支付宝应用 APPID
            private_key: 商户私钥（PEM 格式字符串）
            private_key_path: 商户私钥文件路径
            alipay_public_key: 支付宝公钥（PEM 格式字符串）
            alipay_public_key_path: 支付宝公钥文件路径
            sandbox: 是否使用沙箱环境
            notify_url: 异步通知地址
            return_url: 同步跳转地址
        """
        self.app_id = app_id
        self.sandbox = sandbox
        self.notify_url = notify_url
        self.return_url = return_url

        # 私钥
        if private_key:
            self._private_key = RSA.import_key(private_key)
        elif private_key_path:
            with open(private_key_path) as f:
                self._private_key = RSA.import_key(f.read())
        else:
            raise ValueError("请提供 private_key 或 private_key_path")

        # 支付宝公钥
        if alipay_public_key:
            self._alipay_public_key = alipay_public_key
        elif alipay_public_key_path:
            with open(alipay_public_key_path) as f:
                self._alipay_public_key = f.read()
        else:
            raise ValueError("请提供 alipay_public_key 或 alipay_public_key_path")

        self._base_url = self.SANDBOX_URL if sandbox else self.GATEWAY_URL
        self._headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}

    def _post(self, signed_params: str):
        """Send signed params to Alipay gateway."""
        return requests.post(self._base_url, data=signed_params.encode("utf-8"),
                           headers=self._headers, timeout=30)

    def get_address(self) -> str:
        """支付宝没有地址概念，返回 APPID"""
        return f"ALIPAY:{self.app_id}"

    def sign_transaction(self, transaction_dict: dict) -> dict:
        """支付宝不需要离线签名，直接返回 transaction_dict"""
        return transaction_dict

    def sign_params(self, biz_content: dict) -> str:
        """对请求参数进行 RSA2 签名"""
        params = {
            "app_id": self.app_id,
            "method": biz_content.get("method", "alipay.trade.create"),
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": json.dumps(biz_content, ensure_ascii=False, sort_keys=True, separators=(", ", ": ")),
        }

        # 排序并拼接待签名字符串
        sorted_params = sorted(params.items())
        sign_str = "&".join(f"{k}={v}" for k, v in sorted_params)

        # RSA2 签名
        signer = PKCS1_v1_5.new(self._private_key)
        digest = SHA256.new(sign_str.encode("utf-8"))
        signature = base64.b64encode(signer.sign(digest)).decode("utf-8")

        params["sign"] = signature
        return urlencode(params)

    def create_payment(
        self,
        out_trade_no: str,
        total_amount: float,
        subject: str,
        buyer_id: str,
        product_code: str = "JSAPI_PAY",
        body: str = "",
    ) -> dict:
        """
        创建支付订单。

        Args:
            out_trade_no: 商户订单号（唯一）
            total_amount: 金额（元，精确到分）
            subject: 商品标题
            buyer_id: 买家支付宝 user_id
            product_code: JSAPI_PAY（小程序）或 QUICK_MSECURITY_PAY（APP）
            body: 商品描述（可选）

        Returns:
            API 响应 dict
        """
        biz_content = {
            "method": "alipay.trade.create",
            "out_trade_no": out_trade_no,
            "total_amount": f"{total_amount:.2f}",
            "subject": subject,
            "buyer_id": buyer_id,
            "product_code": product_code,
        }
        if body:
            biz_content["body"] = body
        if self.notify_url:
            biz_content["notify_url"] = self.notify_url

        signed = self.sign_params(biz_content)
        resp = self._post(signed)
        return resp.json()

    def query_payment(self, out_trade_no: str) -> dict:
        """查询支付状态"""
        biz_content = {
            "method": "alipay.trade.query",
            "out_trade_no": out_trade_no,
        }
        signed = self.sign_params(biz_content)
        resp = self._post(signed)
        return resp.json()

    def refund(self, out_trade_no: str, refund_amount: float) -> dict:
        """退款"""
        biz_content = {
            "method": "alipay.trade.refund",
            "out_trade_no": out_trade_no,
            "refund_amount": f"{refund_amount:.2f}",
        }
        signed = self.sign_params(biz_content)
        resp = self._post(signed)
        return resp.json()

    def page_pay(
        self,
        out_trade_no: str,
        total_amount: float,
        subject: str,
        body: str = "",
        return_url: str = "",
    ) -> str:
        """
        电脑网站支付 — alipay.trade.page.pay。

        组装支付页面 GET URL，用户浏览器跳转到此 URL 完成支付。

        Args:
            out_trade_no: 商户订单号（唯一）
            total_amount: 金额（元，精确到分）
            subject: 商品标题
            body: 商品描述（可选）
            return_url: 支付完成后同步跳回地址

        Returns:
            支付宝收银台完整 URL，用户浏览器跳转此地址即可
        """
        biz_content = {
            "method": "alipay.trade.page.pay",
            "out_trade_no": out_trade_no,
            "total_amount": f"{total_amount:.2f}",
            "subject": subject,
            "product_code": "FAST_INSTANT_TRADE_PAY",
        }
        if body:
            biz_content["body"] = body
        if return_url:
            biz_content["return_url"] = return_url
        if self.notify_url:
            biz_content["notify_url"] = self.notify_url

        signed = self.sign_params(biz_content)
        return f"{self._base_url}?{signed}"

    def sign_user_operation(self, user_operation: dict) -> dict:
        return user_operation
