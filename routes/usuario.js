const express = require('express');
const { PrismaClient } = require('@prisma/client');
const { successResponse, errorResponse } = require('../utils/responses');
const { authenticateToken } = require('../middleware/auth');

const router = express.Router();
const prisma = new PrismaClient();

// Get perfil
router.get('/perfil', authenticateToken, async (req, res) => {
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

// Update perfil
router.put('/perfil', authenticateToken, async (req, res) => {
  try {
    const { nome, bio, tema_cor, foto } = req.body;

    const updatedUser = await prisma.user.update({
      where: { id: req.user.id },
      data: {
        ...(nome && { nome }),
        ...(bio && { bio }),
        ...(tema_cor && { tema_cor }),
        ...(foto && { foto })
      }
    });

    return successResponse(res, null, 'Perfil atualizado com sucesso');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Erro interno do servidor', 500);
  }
});

// Upload foto
router.post('/upload-foto', authenticateToken, async (req, res) => {
  try {
    const { foto } = req.body;

    if (!foto) {
      return errorResponse(res, 'Foto é obrigatória', 400);
    }

    await prisma.user.update({
      where: { id: req.user.id },
      data: { foto }
    });

    return successResponse(res, { foto }, 'Foto atualizada com sucesso');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Erro interno do servidor', 500);
  }
});

module.exports = router;