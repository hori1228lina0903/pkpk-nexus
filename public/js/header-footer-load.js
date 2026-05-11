// ヘッダーを読み込む
fetch("/common/header.html")
.then(response => {
if (!response.ok) {
throw new Error("ステータスコードがOKではありません: " + response.status);
}
return response.text();
})
.then(data => {
document.getElementById("header").innerHTML = data;
})
.catch(error => {
console.error("ヘッダーの読み込みに失敗しました:", error);
});

// フッターを読み込む
fetch("/common/footer.html")
.then(response => {
if (!response.ok) {
throw new Error("ステータスコードがOKではありません: " + response.status);
}
return response.text();
})
.then(data => {
document.getElementById("footer").innerHTML = data;
})
.catch(error => {
console.error("フッターの読み込みに失敗しました:", error);
});