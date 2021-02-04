# SNUDAY-server
## 설명
`django rest framework`로 작성하는 스누데이의 서버입니다. 

## 비밀 관리
`.env` 파일을 이용해서 비밀스러운 무언가를 관리합니다. Django의 SECRET_KEY라던가, DB의 password 등은 노출되면 안 됩니다. 
`python-dotenv`를 이용해 관리합니다. 또한 `github action`등을 이용할 때의 비밀 키 등은 해당 레포에서 관리합니다.

## 세팅
`base`에 기본 설정을 놓고, `dev`와 `prod`로 나누어 관리합니다. `DJANGO_SETTINGS_MODULE`을 환경변수로 주어
어떤 세팅을 사용할 것인지 정할 수 있습니다.

## CI / CD
`github action`을 이용해 테스트를 자동으로 진행합니다. 테스트케이스를 잘 작성해서 서버의 안정성을 증명해주세요.
테스트들은 `test_xxx.py`나 `tests.py` 형식인 파일들입니다. 다음은 예시입니다.
```python
res = self.client.patch(
    f'/boards/notice/posts/{self.post.id}/', {
        'content': 'waffle',
    }, format='json'
)
self.assertEqual(res.status_code, 200)
self.assertEqual(res.data['content'], 'waffle')
```
적절한 오류처리가 됨도 다음처럼 보여주세요.
```python
res = self.client.patch(
    f'/boards/notice/posts/{self.post.id}/'
)
self.assertEqual(res.status_code, 400)
```

## 배포
`docker`를 활용합니다. 이미지 빌드는 다음과 같이 합니다.
```bash
docker-compose build
```

실제 구동할 때는 다음과 같이 사용합니다.
```bash
docker-compose pull
docker-compose up -d
```
