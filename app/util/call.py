from twilio.rest import Client

# Twilio 계정 정보
account_sid = 'AC5e938b09a639e17e3a71b42f62e234b4'
auth_token = 'a11cbce7b71e69fa8ada10182191ca79'
twilio_number = '+18059266399'  # 너가 구매한 번호

# 추후 수정
voice_url = 'http://3.37.36.81:5002/voice.xml'  # AWS에서 실행 중인 XML 주소

client = Client(account_sid, auth_token)

def call_user():
    try:
        call = client.calls.create(
            # 수신자 번호(성재 번호)
            to='+82 10 6253 8642',
            # twilio에서 발급받은 전화번호
            from_=twilio_number,
            # xml
            url=voice_url
        )
        print(f"☎️ 전화 발신 완료! Call SID: {call.sid}")
    except Exception as e:
        print(f"❌ 전화 발신 중 오류: {e}")