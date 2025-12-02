# Adicione este endpoint ao auth.py se quiser login mais claro

@router.post("/login-email")
def login_with_email(email: str, password: str, db: Session = Depends(get_db)):
    """Login direto com email e senha"""
    try:
        user = authenticate_user(db, email, password)
        if not user:
            return {"error": "Email ou senha incorretos"}
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }
        
    except Exception as e:
        return {"error": f"Erro: {str(e)}"}