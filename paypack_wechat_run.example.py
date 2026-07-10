"""
PayPack WeChat Pay — 配置模板
复制此文件为 paypack_wechat_run.py 并填入真实凭据
使用前请先登录 pay.weixin.qq.com 获取以下凭据
"""

# ============================================================
# 第一步：去 pay.weixin.qq.com → API安全 → 获取以下3个凭据
# ============================================================

# 1. APIv3 密钥（自己设置一个32位字符串，记下来）
API_V3_KEY = "请填入你的APIv3密钥"

# 2. 证书序列号（在 API证书 页面可以看到）
SERIAL_NO = "请填入证书序列号"

# 3. 商户私钥文件（在 API证书 页面下载 apiclient_key.pem）
PRIVATE_KEY_PATH = "请填入apiclient_key.pem的路径"

# 4. 支付回调地址（需要一个公网可访问的URL）
NOTIFY_URL = "https://你的域名/wechat/notify"

# ============================================================
# 以下不需要改
# ============================================================

MCHID = "请填入你的商户号"
APP_ID = "请填入小程序AppID"
LICENSE_KEY = "PAYPACK-WECHAT-v1-请填入你的LicenseKey"


def create_wechat_pay():
    """创建微信支付实例"""
    from paypack_wechat import WechatSigner
    from paypack import AgentPay

    signer = WechatSigner(
        mchid=MCHID,
        serial_no=SERIAL_NO,
        private_key_path=PRIVATE_KEY_PATH,
        api_v3_key=API_V3_KEY,
        license_key=LICENSE_KEY,
        app_id=APP_ID,
        notify_url=NOTIFY_URL,
    )

    pay = AgentPay(signer=signer, network="wechat")
    return pay


def create_order(openid: str, amount: float, description: str):
    """
    创建微信支付订单（JSAPI）

    Args:
        openid: 微信用户的 openid（小程序里 wx.login 后换取）
        amount: 支付金额（元），如 9.90
        description: 商品描述，如 "AI 数据分析服务"

    Returns:
        prepay_params: 前端拿这个参数调 wx.requestPayment()
    """
    pay = create_wechat_pay()
    result = pay.send(
        to=openid,
        amount=amount,
        currency="CNY",
        subject=description,
        app_id=APP_ID,
    )
    return result


def query_order(out_trade_no: str):
    """查询订单状态"""
    pay = create_wechat_pay()
    result = pay.signer.query_payment(out_trade_no)
    return result


def refund_order(out_trade_no: str, refund_amount: float, reason: str = "AI 退款"):
    """申请退款"""
    pay = create_wechat_pay()
    result = pay.signer.refund(out_trade_no, refund_amount, reason)
    return result


# ============================================================
# 测试：验证配置是否正确（不会真的扣款）
# ============================================================
if __name__ == "__main__":
    missing = []
    if API_V3_KEY == "请填入你的APIv3密钥":
        missing.append("API_V3_KEY")
    if SERIAL_NO == "请填入证书序列号":
        missing.append("SERIAL_NO")
    if PRIVATE_KEY_PATH == "请填入apiclient_key.pem的路径":
        missing.append("PRIVATE_KEY_PATH")

    if missing:
        print("=" * 50)
        print("[!] 请先在微信支付商户平台获取以下凭据：")
        print("=" * 50)
        print()
        print("1. 打开浏览器，登录 https://pay.weixin.qq.com")
        print("2. 顶部菜单 → '账户中心' → 左侧 'API安全'")
        print()
        print("需要获取：")
        print("  a) APIv3密钥 → 点击'设置APIv3密钥'，自己设一个32位字符串")
        print("  b) 证书序列号 → 在'API证书'栏可以看到")
        print("  c) 商户私钥 → 在'API证书'栏下载 apiclient_key.pem")
        print()
        print("当前缺少：")
        for m in missing:
            print(f"  [X] {m}")
        print()
        print("填好后重新运行此脚本即可。")
    else:
        print("配置已就绪，正在初始化...")
        try:
            pay = create_wechat_pay()
            print("[OK] 微信支付初始化成功!")
            print(f"   商户号: {pay.signer.mchid}")
            print(f"   小程序: {APP_ID}")
        except Exception as e:
            print(f"[FAIL] 初始化失败: {e}")
