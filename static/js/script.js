
//Função de devolver

document.addEventListener("DOMContentLoaded", function () {

    const botoes = document.querySelectorAll(".btn-qtd");

    botoes.forEach(function (botao) {

        botao.addEventListener("click", function () {

            const container = botao.closest(
                ".quantidade-devolucao"
            );

            const input = container.querySelector(
                'input[name="quantidade"]'
            );

            let quantidade = parseInt(
                input.value
            );

            const minimo = parseInt(
                input.min
            );

            const maximo = parseInt(
                input.max
            );

            if (botao.dataset.acao === "aumentar") {

                if (quantidade < maximo) {
                    quantidade++;
                }

            }

            if (botao.dataset.acao === "diminuir") {

                if (quantidade > minimo) {
                    quantidade--;
                }

            }

            input.value = quantidade;

        });

    });

});

//autopreencher com a peça do estoque

const inputNome = document.getElementById("nome");
const inputCategoria = document.getElementById("categoria");
const inputQuantidade = document.getElementById("quantidade");
const inputEstoqueMinimo = document.getElementById("estoque_minimo");
const inputPecaId = document.getElementById("peca_id");

const sugestoes = document.getElementById("sugestoes-pecas");
const formularioPeca = document.querySelector(".form[data-editando]");
const editandoPeca = formularioPeca?.dataset.editando === "true";

let timerBusca = null;


function exibirCategoria(categoria) {

    if (!categoria) {
        return "Sem categoria";
    }

    return categoria.charAt(0).toUpperCase() + categoria.slice(1);

}


if (
    inputNome
    && inputCategoria
    && inputQuantidade
    && inputEstoqueMinimo
    && inputPecaId
    && sugestoes
) {

inputNome.addEventListener("input", function () {

    const termo = inputNome.value.trim();

    clearTimeout(timerBusca);

    sugestoes.innerHTML = "";

    // Se apagar o nome, também esquece
    // a peça que estava selecionada
    if (!editandoPeca) {
        inputPecaId.value = "";
    }

    if (termo.length < 2) {
        return;
    }


    timerBusca = setTimeout(function () {

        fetch(
            `/api/pecas/buscar?q=${encodeURIComponent(termo)}`
        )

        .then(response => {

            if (!response.ok) {
                throw new Error(
                    "Erro ao buscar peças."
                );
            }

            return response.json();

        })

        .then(pecas => {

            sugestoes.innerHTML = "";


            if (pecas.length === 0) {
                return;
            }


            pecas.forEach(function (peca) {

                const item = document.createElement("div");

                item.className = "sugestao-peca";


                item.innerHTML = `
                    <div>
                        <strong>${peca.nome}</strong>

                        <small>
                            ${exibirCategoria(peca.categoria)}
                        </small>
                    </div>

                    <span>
                        ${peca.quantidade} unidade(s)
                    </span>
                `;

                item.addEventListener(
                    "click",
                    function () {

                        preencherPeca(peca);

                    }
                );


                sugestoes.appendChild(item);

            });

        })

        .catch(error => {

            console.error(
                "Erro ao buscar peças:",
                error
            );

        });

    }, 250);

});

// preenche os input

function preencherPeca(peca) {

    inputNome.value = peca.nome;

    inputCategoria.value =
        peca.categoria || "";

    inputQuantidade.value =
        peca.quantidade;

    inputEstoqueMinimo.value =
        peca.estoque_minimo;

    inputPecaId.value =
        peca.id;

    sugestoes.innerHTML = "";

}

}


//função de clique geral
document.addEventListener("click", function (event) {

    const linha = event.target.closest(".linha-clicavel");

    if (!linha) {
        return;
    }

    const url = linha.dataset.url;

    if (url) {
        window.location.href = url;
    }

});

// Busca de produto para a saída avulsa de estoque
const formularioSaida = document.querySelector("[data-peca-autocomplete]");

if (formularioSaida) {
    const nomeProduto = formularioSaida.querySelector("#peca_nome");
    const idProduto = formularioSaida.querySelector("#peca_id");
    const sugestoesSaida = formularioSaida.querySelector(".saida-sugestoes");
    const produtoSelecionado = formularioSaida.querySelector(
        ".saida-selected-product"
    );
    let timerBuscaSaida = null;

    nomeProduto.addEventListener("input", function () {
        const termo = nomeProduto.value.trim();
        idProduto.value = "";
        produtoSelecionado.textContent = "Nenhum produto selecionado.";
        sugestoesSaida.innerHTML = "";
        clearTimeout(timerBuscaSaida);

        if (termo.length < 2) {
            return;
        }

        timerBuscaSaida = setTimeout(function () {
            fetch(`/api/pecas/buscar?q=${encodeURIComponent(termo)}`)
                .then(response => response.ok ? response.json() : [])
                .then(pecas => {
                    sugestoesSaida.innerHTML = "";

                    pecas.forEach(function (peca) {
                        const item = document.createElement("button");
                        item.type = "button";
                        item.className = "saida-sugestao-item";
                        item.innerHTML = `<span><strong>${peca.nome}</strong><small>${exibirCategoria(peca.categoria)}</small></span><b>${peca.quantidade} disponível(is)</b>`;

                        item.addEventListener("click", function () {
                            nomeProduto.value = peca.nome;
                            idProduto.value = peca.id;
                            produtoSelecionado.textContent =
                                `${peca.quantidade} unidade(s) disponível(is) em estoque.`;
                            sugestoesSaida.innerHTML = "";
                        });

                        sugestoesSaida.appendChild(item);
                    });
                })
                .catch(() => {
                    sugestoesSaida.innerHTML = "";
                });
        }, 250);
    });

    formularioSaida.addEventListener("submit", function (event) {
        if (!idProduto.value) {
            event.preventDefault();
            produtoSelecionado.textContent =
                "Selecione um produto em uma das sugestões.";
            nomeProduto.focus();
        }
    });
}

