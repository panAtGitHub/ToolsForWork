from flask import Flask, request, jsonify, send_file, after_this_request
from pathlib import Path
import tempfile, shutil, os
from uuid import uuid4
from threading import Thread
from tools.merge_invoice_and_screenshot import merge
from tools.extract_invoice import extract as extract_invoice   # 新增

app = Flask(__name__,
            static_folder="../frontend",
            static_url_path="")

@app.route("/")
def index():
    return app.send_static_file("index.html")

# ----------------------- 任务表 -----------------------
# task_id -> {
#   status: uploading | processing | partial | done | error,
#   pct: 0-100,
#   pdf: str (生成的路径),
#   unpaired: list[str],
#   error: str
# }
tasks = {}

# ---------- 创建【发票信息提取】任务 2025-08-05新增功能2----------
@app.route("/api/extract", methods=["POST"])
def api_create_extract():
    if not request.files:
        return jsonify({"error": "请使用 FormData 上传文件"}), 400

    task_id = uuid4().hex
    tasks[task_id] = {"status": "uploading", "pct": 0, "type": "extract"}

    work_dir = Path(tempfile.mkdtemp(prefix=f"extract_{task_id}_"))
    for f in request.files.getlist("files"):
        dst = work_dir / Path(f.filename)
        dst.parent.mkdir(parents=True, exist_ok=True)
        f.save(dst)

    def _worker():
        try:
            tasks[task_id]["status"] = "processing"

            def report(p): tasks[task_id]["pct"] = p

            txt_path = extract_invoice(str(work_dir), report)
            tasks[task_id].update({
                "status": "done",
                "pct": 100,
                "txt": txt_path
            })
        except Exception as e:
            tasks[task_id] = {"status": "error", "error": str(e)}
        finally:
            pass

    Thread(target=_worker, daemon=True).start()
    return jsonify({"task_id": task_id}), 202



# --------------------- 创建任务 -----------------------
@app.route("/api/merge", methods=["POST"])
def api_create_merge():
    if not request.files:
        return jsonify({"error": "请使用 FormData 上传文件"}), 400

    task_id = uuid4().hex
    tasks[task_id] = {"status": "uploading", "pct": 0}

    # 保存上传文件到临时目录
    work_dir = Path(tempfile.mkdtemp(prefix=f"merge_{task_id}_"))
    for f in request.files.getlist("files"):
        dst = work_dir / Path(f.filename)
        dst.parent.mkdir(parents=True, exist_ok=True)
        f.save(dst)

    inv_ratio = float(request.form.get("inv_ratio", 0.75))

    # 后台线程处理
    def _worker():
        try:
            tasks[task_id]["status"] = "processing"

            def report(p): tasks[task_id]["pct"] = p

            pdf_path, unpaired = merge(str(work_dir), inv_ratio, report)

            tasks[task_id].update({
                "status": "done" if not unpaired else "partial",
                "pct": 100,
                "pdf": pdf_path,
                "unpaired": unpaired
            })
        except Exception as e:
            tasks[task_id] = {"status": "error", "error": str(e)}
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    Thread(target=_worker, daemon=True).start()

    return jsonify({"task_id": task_id}), 202

# --------------------- 进度查询 -----------------------
@app.route("/api/progress/<task_id>")
def api_progress(task_id):
    info = tasks.get(task_id)
    if not info:
        return jsonify({"error": "task not found"}), 404
    return jsonify(info)

# --------------------- 结果下载 -----------------------
@app.route("/api/download/<task_id>")
def api_download(task_id):
    info = tasks.get(task_id)
    if not info:
        return jsonify({"error": "task not found"}), 404

    if info["status"] not in ("done", "partial"):
        return jsonify({"error": "not ready"}), 409

    # 这时 info 里可能有 pdf 或 txt
    file_path = info.get("pdf") or info.get("txt")
    if not file_path or not Path(file_path).exists():
        return jsonify({"error": "file missing"}), 410

    @after_this_request
    def _cleanup(response):
        try:
            # 下载完再删输出文件
            os.remove(file_path)
        except Exception:
            pass
        return response

    return send_file(file_path, as_attachment=True)

# ---------------------- 主入口 ------------------------
if __name__ == "__main__":
    # 本地调试使用 Flask 自带服务器
    app.run(host="0.0.0.0", port=5000, debug=True)
