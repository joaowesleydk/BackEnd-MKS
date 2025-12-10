const express = require('express');
const axios = require('axios');
const { successResponse, errorResponse } = require('../utils/responses');

const router = express.Router();

// Consultar CEP
router.get('/:cep', async (req, res) => {
  try {
    const { cep } = req.params;
    const cleanCep = cep.replace(/\D/g, '');

    if (cleanCep.length !== 8) {
      return errorResponse(res, 'CEP inválido', 400);
    }

    const response = await axios.get(`https://viacep.com.br/ws/${cleanCep}/json/`);
    
    if (response.data.erro) {
      return errorResponse(res, 'CEP não encontrado', 404);
    }

    const address = {
      cep: response.data.cep,
      logradouro: response.data.logradouro,
      bairro: response.data.bairro,
      cidade: response.data.localidade,
      uf: response.data.uf
    };

    return successResponse(res, address, 'CEP encontrado');

  } catch (error) {
    console.error(error);
    return errorResponse(res, 'Erro ao consultar CEP', 500);
  }
});

module.exports = router;