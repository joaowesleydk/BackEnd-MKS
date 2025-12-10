const express = require('express');
const { PrismaClient } = require('@prisma/client');
const { successResponse, errorResponse } = require('../utils/responses');
const { authenticateToken, requireAdmin } = require('../middleware/auth');

const router = express.Router();
const prisma = new PrismaClient();

// Get produtos
router.get('/', async (req, res) => {
  try {
    const { categoria, search, promocao, skip = 0, limit = 50 } = req.query;

    const where = { is_active: true };

    if (categoria) {
      where.categoria = categoria;
    }

    if (search) {
      where.OR = [
        { nome: { contains: search, mode: 'insensitive' } },
        { descricao: { contains: search, mode: 'insensitive' } }
      ];
    }

    if (promocao !== undefined) {
      where.promocao = promocao === 'true';
    }

    const produtos = await prisma.product.findMany({
      where,
      skip: parseInt(skip),
      take: parseInt(limit),
      orderBy: { createdAt: 'desc' }
    });

    return successResponse(res, produtos, 'Produtos listados com sucesso');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Erro interno do servidor', 500);
  }
});

// Get produto by ID
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;

    const produto = await prisma.product.findFirst({
      where: {
        id: parseInt(id),
        is_active: true
      }
    });

    if (!produto) {
      return errorResponse(res, 'Produto não encontrado', 404);
    }

    return successResponse(res, produto, 'Produto encontrado');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Erro interno do servidor', 500);
  }
});

// Create produto (admin only)
router.post('/', authenticateToken, requireAdmin, async (req, res) => {
  try {
    const produto = await prisma.product.create({
      data: req.body
    });

    return successResponse(res, produto, 'Produto criado com sucesso', 201);

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Erro interno do servidor', 500);
  }
});

// Update produto (admin only)
router.put('/:id', authenticateToken, requireAdmin, async (req, res) => {
  try {
    const { id } = req.params;

    const produto = await prisma.product.update({
      where: { id: parseInt(id) },
      data: req.body
    });

    return successResponse(res, produto, 'Produto atualizado com sucesso');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Produto não encontrado', 404);
  }
});

// Delete produto (admin only)
router.delete('/:id', authenticateToken, requireAdmin, async (req, res) => {
  try {
    const { id } = req.params;

    await prisma.product.update({
      where: { id: parseInt(id) },
      data: { is_active: false }
    });

    return successResponse(res, null, 'Produto deletado com sucesso');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Produto não encontrado', 404);
  }
});

module.exports = router;