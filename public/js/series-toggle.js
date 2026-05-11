// トグルの開閉
document.querySelector('.toggle-btn').addEventListener('click', function() {
  const options = document.querySelector('.series-options');
  options.classList.toggle('active');
  this.classList.toggle('active');
});

// フィルター機能
document.querySelectorAll('.series-options button').forEach(btn => {
  btn.addEventListener('click', function() {
    const series = this.dataset.series;
    const buttonText = this.textContent; // "Series A" など
    
    // Showing: をつけて表示
    const selectedSeriesText = document.getElementById('selectedSeriesText');
    selectedSeriesText.textContent = `Showing: ${buttonText}`;
    
    // ボタンの状態更新
    document.querySelectorAll('.series-options button').forEach(b => b.classList.remove('active'));
    this.classList.add('active');
    
    // セットの表示/非表示
    document.querySelectorAll('.content').forEach(set => {
      if (series === 'all' || set.dataset.series === series) {
        set.classList.remove('hidden');
      } else {
        set.classList.add('hidden');
      }
    });
    
    // トグルを閉じる
    document.querySelector('.series-options').classList.remove('active');
    document.querySelector('.toggle-btn').classList.remove('active');
  });
});

// ページ読み込み時
document.addEventListener('DOMContentLoaded', function() {
  const activeButton = document.querySelector('.series-options button.active');
  if (activeButton) {
    const selectedSeriesText = document.getElementById('selectedSeriesText');
    selectedSeriesText.textContent = `Showing: ${activeButton.textContent}`;
  }
});