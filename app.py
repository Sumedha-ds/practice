import os
from http import HTTPStatus

from flask import Flask, jsonify, request

from services import ValidationError, WorkerService


def create_app() -> Flask:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "transcripts.db")
    audio_dir = os.path.join(base_dir, "audio")

    service = WorkerService(db_path=db_path, audio_dir=audio_dir)

    app = Flask(__name__)

    @app.errorhandler(ValidationError)
    def handle_validation_error(err: ValidationError):
        return jsonify({"error": str(err)}), HTTPStatus.BAD_REQUEST

    @app.errorhandler(Exception)
    def handle_unexpected_error(err: Exception):
        app.logger.exception("Unhandled error: %s", err)
        return jsonify({"error": "internal-server-error"}), HTTPStatus.INTERNAL_SERVER_ERROR

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/otp/send")
    def send_otp():
        payload = request.get_json(force=True, silent=True) or {}
        phone = payload.get("phone")
        otp = service.create_otp(phone)
        return jsonify(
            {
                "message": "OTP generated",
                "phone": phone,
                # Returning OTP aids testing; remove for production deployments.
                "demo_otp": otp,
            }
        )

    @app.post("/otp/verify")
    def verify_otp():
        payload = request.get_json(force=True, silent=True) or {}
        phone = payload.get("phone")
        otp = payload.get("otp")
        if not phone or not otp:
            raise ValidationError("Phone and OTP are required.")
        verified = service.verify_otp(phone, otp)
        return jsonify({"verified": verified})

    @app.post("/workers")
    def create_worker():
        payload = request.get_json(force=True, silent=True) or {}
        phone = payload.get("phone")
        answers = payload.get("answers") or {}
        worker_id = service.create_worker(phone, answers)
        return jsonify({"id": worker_id}), HTTPStatus.CREATED

    @app.get("/workers")
    def list_workers():
        workers = service.list_workers()
        return jsonify({"workers": workers})

    @app.post("/transcripts")
    def create_transcript():
        payload = request.get_json(force=True, silent=True) or {}
        text = payload.get("text")
        src_lang = payload.get("source_language")
        tgt_lang = payload.get("target_language")
        generate_audio = bool(payload.get("generate_audio"))
        data = service.create_transcript(
            original_text=text,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            generate_audio=generate_audio,
        )
        return jsonify(data), HTTPStatus.CREATED

    @app.post("/translate")
    def translate():
        payload = request.get_json(force=True, silent=True) or {}
        text = payload.get("text")
        src_lang = payload.get("source_language")
        tgt_lang = payload.get("target_language")
        generate_audio = bool(payload.get("generate_audio"))
        result = service.translate_text(
            text=text,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            generate_audio=generate_audio,
        )
        return jsonify(
            {
                "translated_text": result.translated_text,
                "english_text": result.english_text,
                "audio_path": result.audio_path,
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))


