document.addEventListener("DOMContentLoaded", () => {
  const input   = document.getElementById("merge-files");
  const btn     = document.getElementById("btn-merge");
  const status  = document.getElementById("merge-status");
  const barWrap = document.getElementById("upload-wrapper");
  const bar     = document.getElementById("upload-bar");
  const spinner = document.getElementById("merging-spinner");

  btn.addEventListener("click", () => {
    if (!input.files.length) {
      status.textContent = "请先选择一个文件夹。";
      return;
    }

    /* --- 上传阶段 --- */
    status.textContent = "";
    bar.style.width = "0%";
    barWrap.classList.remove("hidden");
    spinner.classList.add("hidden");

    const fd = new FormData();
    for (const f of input.files) fd.append("files", f, f.webkitRelativePath);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/merge");
    xhr.responseType = "json";

    xhr.upload.onprogress = e => {
      if (e.lengthComputable) bar.style.width = Math.round(e.loaded/e.total*100)+"%";
    };

    xhr.onload = () => {
      if (xhr.status !== 202) {
        barWrap.classList.add("hidden");
        status.textContent = "上传失败：" + xhr.statusText;
        return;
      }
      const { task_id } = xhr.response;
      bar.style.width = "0%";
      spinner.classList.remove("hidden");

      /* --- 轮询进度 --- */
      const timer = setInterval(async () => {
        const res = await fetch(`/api/progress/${task_id}`);
        if (!res.ok) { clearInterval(timer); return; }
        const info = await res.json();

        if (info.status === "processing" || info.status === "uploading") {
          bar.style.width = `${info.pct}%`;
        } else if (info.status === "done" || info.status === "partial") {
          clearInterval(timer);
          bar.style.width = "100%";
          spinner.classList.add("hidden");

          const unpaired = info.unpaired || [];
          if (info.status === "partial") {
            status.innerHTML =
              `已合并，但有 <b>${unpaired.length}</b> 个文件未处理，正在下载…<br>` +
              unpaired.map(n => `• ${n}`).join("<br>");
          } else {
            status.textContent = "合并完成，正在下载…";
          }
          window.location.href = `/api/download/${task_id}`;
        } else if (info.status === "error") {
          clearInterval(timer);
          spinner.classList.add("hidden");
          status.textContent = "合并失败：" + info.error;
        }
      }, 1000);
    };

    xhr.onerror = () => {
      barWrap.classList.add("hidden");
      status.textContent = "网络错误，上传失败。";
    };

    xhr.send(fd);
  });
});


// 加个工具2的相关脚本
function initExtract() {
  const input   = document.getElementById("extract-files");
  const btn     = document.getElementById("btn-extract");
  const barWrap = document.getElementById("extract-progress");
  const bar     = document.getElementById("extract-bar");
  const spin    = document.getElementById("extract-spinner");
  const status  = document.getElementById("extract-status");

  btn.addEventListener("click", () => {
    if (!input.files.length) {
      status.textContent = "请先选择文件夹。";
      return;
    }

    // reset UI
    status.textContent = "";
    bar.style.width = "0%";
    barWrap.classList.remove("hidden");
    spin.classList.add("hidden");

    const fd = new FormData();
    for (const f of input.files) fd.append("files", f, f.webkitRelativePath);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/extract");
    xhr.responseType = "json";

    xhr.upload.onprogress = e => {
      if (e.lengthComputable)
        bar.style.width = Math.round(e.loaded / e.total * 100) + "%";
    };

    xhr.onload = () => {
      if (xhr.status !== 202) {
        barWrap.classList.add("hidden");
        status.textContent = "上传失败：" + xhr.statusText;
        return;
      }
      const { task_id } = xhr.response;
      bar.style.width = "0%";
      spin.classList.remove("hidden");

      const timer = setInterval(async () => {
        const res = await fetch(`/api/progress/${task_id}`);
        if (!res.ok) { clearInterval(timer); return; }
        const info = await res.json();

        if (info.status === "processing") {
          bar.style.width = info.pct + "%";
        } else if (info.status === "done") {
          clearInterval(timer);
          bar.style.width = "100%";
          spin.classList.add("hidden");
          status.textContent = "提取完成，正在下载…";
          window.location.href = `/api/download/${task_id}`;
        } else if (info.status === "error") {
          clearInterval(timer);
          spin.classList.add("hidden");
          status.textContent = "提取失败：" + info.error;
        }
      }, 1000);
    };

    xhr.onerror = () => {
      barWrap.classList.add("hidden");
      status.textContent = "网络错误，上传失败。";
    };

    xhr.send(fd);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  /* 已有的 initMerge() 保持不变 */
  initExtract();   // <— 新增
});
