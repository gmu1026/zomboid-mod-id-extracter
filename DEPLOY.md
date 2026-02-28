# OCI ARM 배포 가이드

대상 환경: Oracle Cloud Infrastructure (Ampere ARM / aarch64), Ubuntu 22.04

> SteamCMD는 호스트에 직접 설치하지 않아도 됩니다.
> API 서버가 작업 처리 시 `sonroyaalmerol/steamcmd-arm64` Docker 이미지를 자동으로 실행합니다.

---

## 1. Docker 설치

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

현재 사용자에게 Docker 권한 부여 (sudo 없이 사용하기 위해):

```bash
sudo usermod -aG docker $USER
newgrp docker
```

설치 확인:

```bash
docker --version
docker compose version
```

---

## 2. 저장소 클론

```bash
git clone https://github.com/gmu1026/zomboid-mod-id-extracter.git
cd zomboid-mod-id-extracter
```

---

## 3. 환경 설정

```bash
cp .env.example .env
```

`.env` 내용은 기본값으로 동작하므로 별도 수정 불필요합니다.
데이터 디렉토리를 미리 생성해 둡니다:

```bash
mkdir -p data/workshop
```

---

## 4. SteamCMD 이미지 사전 pull

첫 요청 시 자동으로 pull되지만, 미리 받아두면 초기 응답이 빠릅니다:

```bash
docker pull sonroyaalmerol/steamcmd-arm64
```

---

## 5. 애플리케이션 실행

```bash
docker compose up -d
```

로그 확인:

```bash
docker compose logs -f
```

---

## 6. OCI 네트워크 포트 오픈

OCI 인스턴스에서 포트 8000을 열어야 외부에서 접근할 수 있습니다.

### 6-1. OCI 콘솔 보안 목록(Security List) 설정

1. OCI 콘솔 → **Networking** → **Virtual Cloud Networks** → 해당 VCN 선택
2. **Security Lists** → 기본 Security List 선택
3. **Add Ingress Rules** 클릭:
   - Source CIDR: `0.0.0.0/0`
   - IP Protocol: `TCP`
   - Destination Port Range: `8000`

### 6-2. 인스턴스 방화벽(iptables) 오픈

OCI Ubuntu 인스턴스는 기본으로 iptables가 포트를 차단합니다:

```bash
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT

# 재부팅 후에도 유지되도록 저장
sudo apt-get install -y iptables-persistent
sudo netfilter-persistent save
```

---

## 7. 동작 확인

```bash
# 서버 상태 확인
curl http://localhost:8000/docs

# 외부에서 접근 (인스턴스 공인 IP 사용)
curl http://<PUBLIC_IP>:8000/docs
```

브라우저에서 `http://<PUBLIC_IP>:8000/docs` 접속 시 Swagger UI가 열립니다.

---

## 8. 업데이트 배포

```bash
git pull origin main
docker compose up -d --build
```

---

## 운영 참고

| 항목 | 내용 |
|------|------|
| 데이터 저장 위치 | `./data/db.sqlite` |
| 다운로드 임시 경로 | `./data/workshop/` (처리 후 자동 삭제) |
| 로그 확인 | `docker compose logs -f api` |
| 서비스 중지 | `docker compose down` |
| 캐시 초기화 | `rm data/db.sqlite` 후 재시작 |
