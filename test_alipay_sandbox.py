"""
支付宝 AI 付通道 — 沙箱测试脚本

使用方法:
  1. 在支付宝开放平台完成开发者入驻后，进入"沙箱"获取沙箱 APPID
  2. 将本项目的公钥 (keys/alipay_public_key_upload.txt) 上传到沙箱
  3. 下载支付宝沙箱公钥，保存为 keys/alipay_sandbox_public_key.pem
  4. 运行: python test_alipay_sandbox.py --appid 你的沙箱APPID

如果入驻卡住，可先访问沙箱直达链接:
  https://openhome.alipay.com/platform/appDaily.htm
"""

import sys
import os
import json

# Add parent to path
sys.path.insert(0, os.path.dirname(__file__))

from paypack.signer.alipay import AlipaySigner
from paypack.core import AgentPay


def test_sandbox(app_id: str):
    """Run Alipay sandbox integration test"""
    key_dir = os.path.join(os.path.dirname(__file__), "paypack", "signer", "keys")

    private_key_path = os.path.join(key_dir, "alipay_private_key.pem")
    alipay_public_key_path = os.path.join(key_dir, "alipay_sandbox_public_key.pem")

    # Check prerequisites
    for path, name in [
        (private_key_path, "商户私钥"),
        (alipay_public_key_path, "支付宝沙箱公钥"),
    ]:
        if not os.path.exists(path):
            print(f"❌ 缺少文件: {name} ({path})")
            if name == "支付宝沙箱公钥":
                print("   → 请从沙箱页面下载支付宝公钥并保存到此路径")
            return False

    print("=" * 60)
    print("  AlipaySigner 沙箱集成测试")
    print("=" * 60)

    # 1. Initialize signer
    print("\n[1/4] 初始化 AlipaySigner ...")
    try:
        signer = AlipaySigner(
            app_id=app_id,
            private_key_path=private_key_path,
            alipay_public_key_path=alipay_public_key_path,
            sandbox=True,  # 沙箱模式
            notify_url="https://rhcjw.com/alipay/notify",
        )
        print(f"  ✅ 签名器已创建 (APPID: {app_id}, 沙箱模式)")
    except Exception as e:
        print(f"  ❌ 初始化失败: {e}")
        return False

    # 2. Test signature generation
    print("\n[2/4] 测试 RSA2 签名 ...")
    try:
        test_biz = {"method": "alipay.trade.query", "out_trade_no": "TEST_001"}
        signed = signer.sign_params(test_biz)
        print(f"  ✅ 签名生成成功 ({len(signed)} 字节)")
    except Exception as e:
        print(f"  ❌ 签名失败: {e}")
        return False

    # 3. Test AgentPay integration
    print("\n[3/4] 测试 AgentPay 集成 ...")
    try:
        pay = AgentPay(signer=signer, network="alipay")
        addr = signer.get_address()
        print(f"  ✅ AgentPay 初始化成功 (地址: {addr})")
    except Exception as e:
        print(f"  ❌ AgentPay 初始化失败: {e}")
        return False

    # 4. Test API call (query non-existent order - should return "not exist" not "auth error")
    print("\n[4/4] 测试沙箱 API 连通性 ...")
    print("  → 发送 alipay.trade.query 请求...")
    try:
        result = signer.query_payment("PAYPACK_SANDBOX_TEST_001")
        code = result.get("alipay_trade_query_response", {}).get("code", "")
        sub_msg = result.get("alipay_trade_query_response", {}).get("sub_msg", "")

        if code == "40004":  # "Business Failed" - expected for non-existent order
            print(f"  ✅ API 连通正常! 订单不存在(预期): {sub_msg}")
            return True
        elif code == "10000":  # Success
            print(f"  ✅ API 连通正常, 查询成功")
            return True
        elif "40002" in code or "无效" in sub_msg or "invalid" in sub_msg.lower():
            print(f"  ⚠️  API 通了但签名/APPID有误: code={code}, msg={sub_msg}")
            print("  → 请确认: 1)公钥已上传到沙箱 2)APPID正确 3)沙箱公钥正确")
            return False
        elif "40001" in code:
            print(f"  ⚠️  认证失败 (code=40001): {sub_msg}")
            print("  → 请确认 private_key 和 APPID 匹配")
            return False
        else:
            print(f"  ⚠️  未知响应: code={code}, msg={sub_msg}")
            print(f"  完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return False

    except Exception as e:
        print(f"  ❌ 网络异常: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        print("\n用法: python test_alipay_sandbox.py <沙箱APPID>")
        print("示例: python test_alipay_sandbox.py 2021000123456789")
        sys.exit(0)

    app_id = sys.argv[1].strip()
    success = test_sandbox(app_id)
    sys.exit(0 if success else 1)
