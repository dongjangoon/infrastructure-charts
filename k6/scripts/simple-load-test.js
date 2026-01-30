import http from 'k6/http';
import { check, sleep } from 'k6';

// 간단한 부하 테스트 설정
export let options = {
  stages: [
    { duration: '2m', target: 20 },   // 2분 동안 20 사용자로 증가
    { duration: '5m', target: 20 },   // 5분 동안 20 사용자 유지
    { duration: '2m', target: 40 },   // 2분 동안 40 사용자로 증가
    { duration: '5m', target: 40 },   // 5분 동안 40 사용자 유지
    { duration: '2m', target: 0 },    // 2분 동안 0으로 감소
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.1'],
  },
};

const BASE_URL = 'http://test-app-service.default.svc.cluster.local';

export default function () {
  let response = http.get(BASE_URL);
  
  check(response, {
    'status is 200': (r) => r.status === 200,
  });

  sleep(1);
}