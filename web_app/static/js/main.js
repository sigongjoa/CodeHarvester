document.addEventListener('DOMContentLoaded', function() {
    // 플래시 메시지 자동 닫기
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // 코드 하이라이팅 초기화 (코드 보기 페이지에서 사용)
    if (typeof hljs !== 'undefined') {
        hljs.highlightAll();
    }

    // 툴팁 초기화
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 차트 초기화 함수 (통계 페이지에서 사용)
    window.initCharts = function(statsData) {
        if (!statsData || typeof Chart === 'undefined') return;

        // 저장소별 파일 수 차트
        if (document.getElementById('repoChart') && statsData.repositories) {
            const repoCtx = document.getElementById('repoChart').getContext('2d');
            new Chart(repoCtx, {
                type: 'bar',
                data: {
                    labels: statsData.repositories.map(repo => repo.name),
                    datasets: [{
                        label: '파일 수',
                        data: statsData.repositories.map(repo => repo.file_count),
                        backgroundColor: 'rgba(54, 162, 235, 0.7)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: '파일 수'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: '저장소'
                            }
                        }
                    }
                }
            });
        }

        // 품질 점수 분포 차트
        if (document.getElementById('qualityChart') && statsData.quality_distribution) {
            const qualityCtx = document.getElementById('qualityChart').getContext('2d');
            new Chart(qualityCtx, {
                type: 'bar',
                data: {
                    labels: ['0-2', '2-4', '4-6', '6-8', '8-10'],
                    datasets: [{
                        label: '파일 수',
                        data: statsData.quality_distribution,
                        backgroundColor: 'rgba(255, 99, 132, 0.7)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: '파일 수'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: '품질 점수 범위'
                            }
                        }
                    }
                }
            });
        }

        // 태그 분포 차트
        if (document.getElementById('tagChart') && statsData.tags && statsData.tags.length > 0) {
            const tagCtx = document.getElementById('tagChart').getContext('2d');
            const colors = [
                'rgba(54, 162, 235, 0.7)',
                'rgba(255, 99, 132, 0.7)',
                'rgba(75, 192, 192, 0.7)',
                'rgba(255, 159, 64, 0.7)',
                'rgba(153, 102, 255, 0.7)',
                'rgba(255, 205, 86, 0.7)',
                'rgba(201, 203, 207, 0.7)'
            ];
            
            new Chart(tagCtx, {
                type: 'pie',
                data: {
                    labels: statsData.tags.map(tag => tag.name),
                    datasets: [{
                        data: statsData.tags.map(tag => tag.count),
                        backgroundColor: colors.slice(0, statsData.tags.length),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right'
                        }
                    }
                }
            });
        }
    };

    // 통계 페이지 초기화
    if (document.getElementById('stats-content')) {
        fetch('/code/api/stats')
            .then(response => response.json())
            .then(data => {
                // 데이터를 콘솔에 출력하여 확인
                console.log("받은 데이터:", data);
                
                // 기본 통계 업데이트
                document.getElementById('repo-count').textContent = data.repository_count || 0;
                document.getElementById('file-count').textContent = data.file_count || 0;
                document.getElementById('suitable-count').textContent = data.suitable_file_count || 0;
                document.getElementById('avg-quality').textContent = (data.average_quality_score || 0).toFixed(1);
                
                // 차트 초기화
                window.initCharts(data);
                
                // 로딩 화면 숨기기, 실제 내용 표시
                document.getElementById('stats-loading').classList.add('d-none');
                document.getElementById('stats-content').classList.remove('d-none');
            })
            .catch(error => {
                console.error('통계 정보 가져오기 오류:', error);
                document.getElementById('stats-loading').innerHTML = '<div class="alert alert-danger">통계 정보를 가져오는 중 오류가 발생했습니다.</div>';
            });    
    }
});
