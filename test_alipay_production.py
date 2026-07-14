"""
支付宝 AI 付通道 -- 生产环境验证脚本

验证 AlipaySigner 生产配置是否正确:
  1. RSA2 签名生成
  2. AgentPay 集成（离链模式）
  3. API 连通性测试（查单）

Usage:
    python test_alipay_production.py
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

from paypack.signer.alipay import AlipaySigner
from paypack.core import AgentPay


def test_production():
    """Run Alipay production integration test"""
    key_dir = os.path.join(os.path.dirname(__file__), "paypack", "signer", "keys")

    private_key_path = os.path.join(key_dir, "alipay_private_key.pem")
    alipay_public_key_path = os.path.join(key_dir, "alipay_production_public_key.pem")
    app_id = "2021006170636644"

    # Check prerequisites
    for path, name in [
        (private_key_path, "商户私钥"),
        (alipay_public_key_path, "支付宝公钥"),
    ]:
        if not os.path.exists(path):
            print(f"[X] 缺少文件: {name} ({path})")
            return False

    print("=" * 60)
    print("  AlipaySigner 生产环境验证")
    print("=" * 60)
    print(f"  APPID: {app_id}")

    # 1. Initialize signer
    print("\n[1/4] 初始化 AlipaySigner (生产模式)...")
    try:
        signer = AlipaySigner(
            app_id=app_id,
            private_key_path=private_key_path,
            alipay_public_key_path=alipay_public_key_path,
            sandbox=False,
            notify_url="https://rhcjw.com/alipay/notify",
        )
        print(f"  [OK] 签名器已创建")
    except Exception as e:
        print(f"  [X] 初始化失败: {e}")
        return False

    # 2. Test RSA2 signature
    print("\n[2/4] 测试 RSA2 签名 ...")
    try:
        test_biz = {"method": "alipay.trade.query", "out_trade_no": "PAYPACK_PROD_TEST_001"}
        signed = signer.sign_params(test_biz)
        print(f"  [OK] 签名生成成功 ({len(signed)} 字节)")
    except Exception as e:
        print(f"  [X] 签名失败: {e}")
        return False

    # 3. Test AgentPay integration
    print("\n[3/4] 测试 AgentPay 集成 (离链模式)...")
    try:
        pay = AgentPay(signer=signer, network="alipay")
        addr = signer.get_address()
        print(f"  [OK] AgentPay 初始化成功 (地址: {addr})")
    except Exception as e:
        print(f"  [X] AgentPay 初始化失败: {e}")
        return False

    # 4. Test API connectivity
    print("\n[4/4] 测试支付宝生产 API 连通性 ...")
    print("  -> 发送 alipay.trade.query 请求...")
    try:
        result = signer.query_payment("PAYPACK_PROD_TEST_001")
        resp = result.get("alipay_trade_query_response", {})
        code = resp.get("code", "")
        sub_msg = resp.get("sub_msg", "")
        msg = resp.get("msg", "")
        print(f"  响应: code={code}, msg={msg}, sub_msg={sub_msg}")

        if code == "40004":
            print(f"  [OK] API 连通正常! (订单不存在, 预期行为)")
            return True
        elif code == "10000":
            print(f"  [OK] API 连通正常, 查询成功")
            return True
        else:
            print(f"  [?] {json.dumps(result, ensure_ascii=False, indent=2)}")
            return False
    except Exception as e:
        print(f"  [X] 网络异常: {e}")
        return False


if __name__ == "__main__":
    success = test_production()
    if success:
        print("\n" + "=" * 60)
        print("  生产环境配置验证通过!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("  [X] 验证失败，请检查配置")
        print("=" * 60)
        sys.exit(1)
