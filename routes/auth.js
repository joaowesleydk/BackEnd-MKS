const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { OAuth2Client } = require('google-auth-library');
const { PrismaClient } = require('@prisma/client');
const { successResponse, errorResponse } = require('../utils/responses');
const { authenticateToken } = require('../middleware/auth');

const router = express.Router();
const prisma = new PrismaClient();
const googleClient = new OAuth2Client(process.env.GOOGLE_CLIENT_ID);

const generateToken = (user) => {
  return jwt.sign(
    { 
      user_id: user.id, 
      email: user.email, 
      role: user.role 
    },
    process.env.JWT_SECRET_KEY,
    { expiresIn: '24h' }
  );
};

// Register
router.post('/register', async (req, res) => {
  try {
    const { email, password, nome } = req.body;

    const existingUser = await prisma.user.findUnique({
      where: { email }
    });

    if (existingUser) {
      return errorResponse(res, 'Email já cadastrado', 400);
    }

    const hashedPassword = await bcrypt.hash(password, 10);

    const user = await prisma.user.create({
      data: {
        email,
        password: hashedPassword,
        nome
      }
    });

    const token = generateToken(user);

    return successResponse(res, {
      access_token: token,
      token_type: 'bearer',
      user: {
        id: user.id,
        email: user.email,
        nome: user.nome,
        role: user.role
      }
    }, 'Usuário registrado com sucesso');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Erro interno do servidor', 500);
  }
});

// Login
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    const user = await prisma.user.findUnique({
      where: { email }
    });

    if (!user || !user.password) {
      return errorResponse(res, 'Credenciais inválidas', 401);
    }

    const validPassword = await bcrypt.compare(password, user.password);
    if (!validPassword) {
      return errorResponse(res, 'Credenciais inválidas', 401);
    }

    const token = generateToken(user);

    return successResponse(res, {
      access_token: token,
      token_type: 'bearer',
      user: {
        id: user.id,
        email: user.email,
        nome: user.nome,
        role: user.role
      }
    }, 'Login realizado com sucesso');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Erro interno do servidor', 500);
  }
});

// Google Login
router.post('/google', async (req, res) => {
  try {
    const { token } = req.body;

    const ticket = await googleClient.verifyIdToken({
      idToken: token,
      audience: process.env.GOOGLE_CLIENT_ID
    });

    const payload = ticket.getPayload();
    const { sub: google_id, email, name: nome, picture: foto } = payload;

    let user = await prisma.user.findUnique({
      where: { email }
    });

    if (!user) {
      user = await prisma.user.create({
        data: {
          email,
          nome,
          foto,
          google_id
        }
      });
    }

    const accessToken = generateToken(user);

    return successResponse(res, {
      access_token: accessToken,
      token_type: 'bearer',
      user: {
        id: user.id,
        email: user.email,
        nome: user.nome,
        role: user.role
      }
    }, 'Login Google realizado com sucesso');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Token Google inválido', 401);
  }
});

// Get Profile
router.get('/me', authenticateToken, async (req, res) => {
  return successResponse(res, {
    id: req.user.id,
    email: req.user.email,
    nome: req.user.nome,
    foto: req.user.foto,
    bio: req.user.bio,
    tema_cor: req.user.tema_cor,
    role: req.user.role
  }, 'Perfil carregado');
});

module.exports = router;