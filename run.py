from app import create_app

app = create_app()

if __name__ == '__main__':
    # Running on 0.0.0.0 makes it accessible on your local network/Render
    app.run(host='0.0.0.0', port=5000, debug=True)