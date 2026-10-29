# Deploying DermaLens (free, about 15 minutes)

## 0. Test it locally the same way production runs it
    cd backend
    pip install -r requirements.txt
    python -c "import wsgi; print('ok')"        # creates + seeds the database
    python -m app.main

## 1. Put the project on GitHub
    cd dermalens
    git init
    git add .
    git commit -m "DermaLens"
    # create an empty repo on github.com, then:
    git remote add origin https://github.com/<you>/dermalens.git
    git branch -M main
    git push -u origin main

## 2. Deploy on Render (render.com, sign in with GitHub)
1. New + > Web Service > pick your repo. Render finds the `Dockerfile` (or use New + > Blueprint to use `render.yaml`).
2. Instance type: Free. Add environment variable `DERMALENS_SECRET` = any long random text.
3. Create. The first build takes 5-10 minutes. You get a URL like https://dermalens.onrender.com .
4. Make yourself admin: on the service page open "Shell" (paid) or, on free, use the trick below.

## Free-tier limits (say these in your viva)
- The free server sleeps after ~15 minutes idle; the first visit then takes ~30-60 s. Open the site once before your demo.
- Free disk is not permanent: the database resets on every redeploy/restart, so accounts and shared routines vanish
  and the sample data is re-loaded. Fine for a demo. For permanent data use a paid disk mounted at /data.
- Making an admin without a shell: set the env var `DERMALENS_ADMIN_EMAIL` to your email, sign up with it, restart.
- Camera needs HTTPS, which Render provides, so the camera scanner works online (not on plain http except localhost).
- Free instances have 512 MB RAM; if it runs out of memory, change `-w 2` to `-w 1` in the Dockerfile.

## Other hosts
Any host that runs a Docker image works (Railway, Fly.io, Google Cloud Run). The app listens on `$PORT`.
PythonAnywhere (no Docker): upload the folder, point the WSGI file at `wsgi:app`; OCR will not work there.
