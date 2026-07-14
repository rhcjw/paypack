"""
支付宝生产环境 -- 真实支付测试

生成电脑网站支付链接，浏览器打开后用支付宝扫码付款。
支付成功后自动查询结果。

Usage:
    python test_alipay_pay.py
"""
import sys
import os
import time
import json
import webbrowser

sys.path.insert(0, os.path.dirname(__file__))

from paypack.signer.alipay import AlipaySigner


def main():
    key_dir = os.path.join(os.path.dirname(__file__), "paypack", "signer", "keys")
    private_key_path = os.path.join(key_dir, "alipay_private_key.pem")
    alipay_public_key_path = os.path.join(key_dir, "alipay_production_public_key.pem")
    app_id = "2021006170636644"

    # 初始化签名器
    print("=" * 60)
    print("  支付宝真实支付测试")
    print("=" * 60)
    print(f"  APPID: {app_id}")

    signer = AlipaySigner(
        app_id=app_id,
        private_key_path=private_key_path,
        alipay_public_key_path=alipay_public_key_path,
        sandbox=False,
        notify_url="https://rhcjw.com/alipay/notify",
        return_url="https://rhcjw.com/alipay/return",
    )
    print("  [OK] 签名器初始化成功\n")

    # 生成订单号
    import uuid
    out_trade_no = f"PAYPACK_REAL_TEST_{int(time.time())}"
    amount = 0.01  # 1分钱测试
    subject = "PayPack AI 支付测试"

    print(f"  订单号: {out_trade_no}")
    print(f"  金额: {amount} 元")
    print(f"  商品: {subject}")

    # 生成支付 URL
    print("\n[1/2] 生成支付链接...")
    pay_url = signer.page_pay(
        out_trade_no=out_trade_no,
        total_amount=amount,
        subject=subject,
        body="PayPack 生产环境支付功能验证测试",
        return_url="https://rhcjw.com/alipay/return",
    )
    print(f"  [OK] 支付链接已生成\n")
    print(f"  >>> 支付链接 ({len(pay_url)} 字符):")
    print(f"  {pay_url[:80]}...")
    print(f"\n  >>> 请在浏览器中打开此链接，用支付宝扫码付款 <<<")

    # 尝试自动打开浏览器
    try:
        webbrowser.open(pay_url)
        print("  [INFO] 已自动打开浏览器")
    except Exception:
        pass

    # 轮询查询支付结果
    print(f"\n[2/2] 等待支付 (每5秒查询一次, 最多等120秒)...")
    print("  请用支付宝扫码完成支付!")
    for i in range(24):  # 最多等120秒
        time.sleep(5)
        try:
            result = signer.query_payment(out_trade_no)
            resp = result.get("alipay_trade_query_response", {})
            trade_status = resp.get("trade_status", "")
            code = resp.get("code", "")

            if trade_status == "TRADE_SUCCESS":
                print(f"\n  [OK] 支付成功!")
                print(f"  ----------------------------------------")
                print(f"  订单号:   {out_trade_no}")
                print(f"  金额:     {resp.get('total_amount', '?')} 元")
                print(f"  状态:     {trade_status}")
                print(f"  买家:     {resp.get('buyer_user_id', '?')}")
                print(f"  支付宝:   {resp.get('buyer_logon_id', '?')}")
                print(f"  时间:     {resp.get('send_pay_date', '?')}")
                print(f"  ----------------------------------------")
                return True
            elif trade_status == "TRADE_CLOSED":
                print(f"  [X] 订单已关闭")
                return False
            elif code == "40004":
                dot = "." * ((i % 4) + 1)
                print(f"  \r  等待支付{dot:<4}", end="", flush=True)
            else:
                print(f"  [?] 响应: code={code}, status={trade_status}")
        except Exception as e:
            print(f"  [X] 查询异常: {e}")

    print(f"\n  [X] 等待超时，支付未完成")
    print(f"  您仍可以手动在浏览器打开链接完成支付")
    return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n" + "=" * 60)
        print("  支付测试通过! 支付宝生产环境集成完成!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("  支付未完成，脚本退出(不影响后续)")
        print("=" * 60)
