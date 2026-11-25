
//Função de devolver

const formularioMaquina = document.querySelector("#patrimonios-maquinas");

if (formularioMaquina) {
    const inputPatrimonio = document.getElementById("patrimonio");
    const inputEmpresa = document.getElementById("empresa");
    const inputTipo = document.getElementById("tipo");
    const inputModelo = document.getElementById("modelo");
    const patrimonios = JSON.parse(formularioMaquina.textContent || "{}");

    function preencherIdentificadorMaquina() {
        const valor = inputPatrimonio.value.trim().toUpperCase();
        const partes = valor.match(/^([^-]+)-([^-]+)-([ND])$/);

        if (partes) {
            inputPatrimonio.value = partes[1];
            inputEmpresa.value = partes[2];
            inputTipo.value = partes[3] === "N" ? "notebook" : "desktop";
            const dados = patrimonios[partes[1]];
            if (dados?.modelo && inputModelo) inputModelo.value = dados.modelo;
            document.getElementById("status_maquina").value = "Em estoque";
            return;
        }

        const dados = patrimonios[valor];
        if (dados) {
            inputEmpresa.value = dados.empresa;
            inputTipo.value = dados.tipo;
            if (dados.modelo && inputModelo) inputModelo.value = dados.modelo;
            document.getElementById("status_maquina").value = "Em estoque";
        }
    }

    inputPatrimonio.addEventListener("input", preencherIdentificadorMaquina);
    inputPatrimonio.addEventListener("change", preencherIdentificadorMaquina);
}

const formularioAtendimento = document.querySelector("#patrimonios-atendimento");
if (formularioAtendimento) {
    const inputPatrimonioAtendimento = document.getElementById("patrimonio");
    const patrimoniosAtendimento = JSON.parse(formularioAtendimento.textContent || "{}");

    inputPatrimonioAtendimento.addEventListener("blur", function () {
        const valor = inputPatrimonioAtendimento.value.trim().toUpperCase();
        const identificador = patrimoniosAtendimento[valor];
        if (identificador) inputPatrimonioAtendimento.value = identificador;
    });
}

document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll("[data-table-search]").forEach(function (input) {
        const table = document.getElementById(input.dataset.tableSearch);
        if (!table) return;

        const tbody = table.querySelector("tbody");
        const rows = Array.from(tbody.querySelectorAll("tr:not(.table-empty-row)"));
        const initialEmptyRow = tbody.querySelector(".table-empty-row");
        const count = document.querySelector(
            `[data-search-count="${input.dataset.tableSearch}"]`
        );
        const noResultsRow = document.createElement("tr");
        noResultsRow.className = "table-search-empty";
        noResultsRow.hidden = true;
        noResultsRow.innerHTML = `<td colspan="${table.querySelectorAll("thead th").length}"></td>`;
        noResultsRow.querySelector("td").textContent = table.dataset.searchEmpty;
        tbody.appendChild(noResultsRow);

        function normalize(text) {
            return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR");
        }

        function filterRows() {
            const query = normalize(input.value.trim());
            let visibleCount = 0;

            rows.forEach(function (row) {
                const matches = normalize(row.innerText).includes(query);
                row.hidden = !matches;
                if (matches) visibleCount++;
            });

            if (initialEmptyRow) initialEmptyRow.hidden = Boolean(query);
            noResultsRow.hidden = !query || visibleCount > 0;
            if (count) {
                count.textContent = query
                    ? `${visibleCount} resultado${visibleCount === 1 ? "" : "s"}`
                    : `${rows.length} registro${rows.length === 1 ? "" : "s"}`;
            }
        }

        input.addEventListener("input", filterRows);
        filterRows();
    });

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

// Busca máquinas disponíveis para saída por patrimônio, tipo ou modelo.
const formularioSaidaMaquina = document.querySelector(".saida-machine-form");

if (formularioSaidaMaquina) {
    const buscaMaquina = formularioSaidaMaquina.querySelector("#maquina_busca");
    const idMaquina = formularioSaidaMaquina.querySelector("#maquina_id");
    const sugestoesMaquina = formularioSaidaMaquina.querySelector(".saida-maquina-sugestoes");
    const maquinaSelecionada = formularioSaidaMaquina.querySelector("#maquina-selecionada");
    let timerBuscaMaquina = null;

    buscaMaquina.addEventListener("input", function () {
        const termo = buscaMaquina.value.trim();
        idMaquina.value = "";
        maquinaSelecionada.textContent = "Nenhuma máquina selecionada.";
        sugestoesMaquina.innerHTML = "";
        clearTimeout(timerBuscaMaquina);

        if (!termo) return;

        timerBuscaMaquina = setTimeout(function () {
            fetch(`/api/maquinas/estoque/buscar?q=${encodeURIComponent(termo)}`)
                .then(response => response.ok ? response.json() : [])
                .then(maquinas => {
                    sugestoesMaquina.innerHTML = "";

                    if (!maquinas.length) {
                        const vazio = document.createElement("div");
                        vazio.className = "saida-sugestao-vazia";
                        vazio.textContent = "Nenhuma máquina encontrada no estoque.";
                        sugestoesMaquina.appendChild(vazio);
                        return;
                    }

                    maquinas.forEach(function (maquina) {
                        const item = document.createElement("button");
                        const texto = document.createElement("span");
                        const identificador = document.createElement("strong");
                        const modelo = document.createElement("small");

                        item.type = "button";
                        item.className = "saida-sugestao-item";
                        identificador.textContent = maquina.identificador;
                        modelo.textContent = maquina.modelo;
                        texto.append(identificador, modelo);
                        item.appendChild(texto);
                        item.addEventListener("click", function () {
                            buscaMaquina.value = maquina.identificador;
                            idMaquina.value = maquina.id;
                            maquinaSelecionada.textContent = `Selecionada: ${maquina.identificador} — ${maquina.modelo}`;
                            sugestoesMaquina.innerHTML = "";
                        });
                        sugestoesMaquina.appendChild(item);
                    });
                })
                .catch(() => {
                    sugestoesMaquina.innerHTML = "";
                });
        }, 180);
    });

    formularioSaidaMaquina.addEventListener("submit", function (event) {
        if (!idMaquina.value) {
            event.preventDefault();
            maquinaSelecionada.textContent = "Digite e selecione uma máquina nas sugestões.";
            buscaMaquina.focus();
        }
    });
}

