from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    print("""
  ╔═══════════════════════════════════════════════╗
  ║     TrustBond API Server                      ║
  ║     Rwanda National Police                    ║
  ╠═══════════════════════════════════════════════╣
  ║  Status:  Running                             ║
  ║  Port:    5000                                ║
  ║  Mode:    Development                         ║
  ║  Database: PostgreSQL                         ║
  ╚═══════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
