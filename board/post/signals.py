from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import Reply

@receiver(post_save, sender=Reply)
def send_reply_notification(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        author = post.author
        reply_author = instance.author

        if author.email:
            subject = f'Новый отклик на ваше объявление "{post.title}"'
            html_message = render_to_string(
                'email/reply_notification.html',
                {'post': post, 'reply': instance, 'reply_author': reply_author}
            )
            send_mail(
                subject,
                '',
                'maximssshepelev@yandex.ru',
                [author.email],
                html_message=html_message,
                fail_silently=False
            )