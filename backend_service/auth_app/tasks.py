from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


@shared_task
def send_approval_email(user_email, first_name, role):
    subject = "🎉 You're Approved — Welcome to Vestique!"

    role_display = role.replace("_", " ").title()
    login_url = "http://localhost:5173/login"

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Welcome to Vestique</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1a1a1a 0%,#2d2d2d 100%);padding:48px 40px;text-align:center;">
              <h1 style="margin:0;color:#ffffff;font-size:32px;font-weight:800;letter-spacing:4px;text-transform:uppercase;">VESTIQUE</h1>
              <p style="margin:8px 0 0;color:#a0a0a0;font-size:13px;letter-spacing:2px;text-transform:uppercase;">Fashion Platform</p>
            </td>
          </tr>

          <!-- Green approved badge -->
          <tr>
            <td style="background:#f0fdf4;padding:32px 40px;text-align:center;border-bottom:1px solid #dcfce7;">
              <div style="display:inline-block;background:#22c55e;border-radius:50%;width:64px;height:64px;line-height:64px;text-align:center;font-size:28px;margin-bottom:16px;">✓</div>
              <h2 style="margin:0;color:#15803d;font-size:22px;font-weight:700;">Your Account is Approved!</h2>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px 40px 32px;">
              <p style="margin:0 0 20px;color:#374151;font-size:16px;line-height:1.6;">
                Hi <strong>{first_name}</strong>,
              </p>
              <p style="margin:0 0 20px;color:#374151;font-size:16px;line-height:1.6;">
                Great news! Our team has reviewed your application and your <strong>{role_display}</strong> account on Vestique has been <strong style="color:#15803d;">officially approved</strong>.
              </p>
              <p style="margin:0 0 32px;color:#374151;font-size:16px;line-height:1.6;">
                You now have full access to the platform. Connect with clients, showcase your work, and grow your fashion business with Vestique.
              </p>

              <!-- What's next box -->
              <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;border-radius:12px;border:1px solid #e5e7eb;margin-bottom:32px;">
                <tr>
                  <td style="padding:24px 28px;">
                    <p style="margin:0 0 16px;color:#111827;font-size:15px;font-weight:700;text-transform:uppercase;letter-spacing:1px;">What's Next</p>
                    <table cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="padding:6px 0;color:#374151;font-size:14px;">🎨 &nbsp; Complete your profile</td>
                      </tr>
                      <tr>
                        <td style="padding:6px 0;color:#374151;font-size:14px;">📸 &nbsp; Upload your portfolio</td>
                      </tr>
                      <tr>
                        <td style="padding:6px 0;color:#374151;font-size:14px;">🤝 &nbsp; Connect with customers</td>
                      </tr>
                      <tr>
                        <td style="padding:6px 0;color:#374151;font-size:14px;">💬 &nbsp; Start receiving orders</td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- CTA Button -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center">
                    <a href="{login_url}" style="display:inline-block;background:#1a1a1a;color:#ffffff;text-decoration:none;padding:16px 48px;border-radius:10px;font-size:15px;font-weight:700;letter-spacing:1px;text-transform:uppercase;">
                      Login to Vestique →
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#f9fafb;padding:24px 40px;text-align:center;border-top:1px solid #e5e7eb;">
              <p style="margin:0;color:#9ca3af;font-size:12px;line-height:1.6;">
                You're receiving this email because you registered as a <strong>{role_display}</strong> on Vestique.<br/>
                © 2024 Vestique. All rights reserved.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    text_content = f"Hi {first_name}, your Vestique {role_display} account has been approved! Login at {login_url}"

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user_email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()