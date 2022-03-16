from rest_framework.exceptions import APIException


class NoSubscriberInPrivateChannel(APIException):
    status_code = 400
    default_detail = "비공개 채널에 구독자가 한 명도 없어, 비공개 채널에 접근할 수 없습니다."
    default_code = "no_subscriber_in_private_channel"
