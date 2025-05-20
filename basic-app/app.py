from shiny import App, ui, reactive, render

# Estoque inicial de produtos
product_stock = {
    "Alface": {"preco": 6.00, "quantidade": 10},
    "Tomate": {"preco": 11.00, "quantidade": 8},
    "Batata": {"preco": 9.00, "quantidade": 15},
    "Chocolate": {"preco": 5.00, "quantidade": 20},
    "Banana": {"preco": 3.50, "quantidade": 12}
}

# Gera a tabela HTML com os produtos
def render_table():
    return ui.tags.table(
        {"class": "table table-striped"},
        ui.tags.thead(
            ui.tags.tr(
                ui.tags.th("Produto"),
                ui.tags.th("Preço (R$)"),
                ui.tags.th("Estoque")
            )
        ),
        ui.tags.tbody(
            *[
                ui.tags.tr(
                    ui.tags.td(prod),
                    ui.tags.td(f"{info['preco']:.2f}"),
                    ui.tags.td(info["quantidade"])
                )
                for prod, info in product_stock.items()
            ]
        )
    )

# Inputs numéricos para cada produto
def render_inputs():
    input_columns = []

    for i, (prod, info) in enumerate(product_stock.items()):
        col = ui.column(
            6,  # largura de 6 colunas (em um total de 12, então cabem 2 por linha)
            ui.input_numeric(
                f"quant_{prod}",
                prod,
                min=0,
                max=info['quantidade'],
                value=0
            )
        )
        input_columns.append(col)

    # Agrupa inputs em linhas de duas colunas
    rows = []
    for i in range(0, len(input_columns), 2):
        rows.append(ui.row(*input_columns[i:i+2]))

    return ui.div(
        ui.h5("Escolha a quantidade de cada produto:"),
        *rows
    )


# Interface
app_ui = ui.page_fluid(
    ui.panel_title("Mercadinho Unasp - Caixa de Supermercado"),
    ui.output_ui("product_table"),
    ui.output_ui("product_inputs"),
    ui.output_text("total_value"),
    ui.input_action_button("finalize_purchase", "Finalizar Compra")
)

# Lógica do servidor
def server(input, output, session):
    @output
    @render.ui
    def product_table():
        return render_table()

    @output
    @render.ui
    def product_inputs():
        return render_inputs()

    @reactive.Calc
    def total_value_calc():
        total = 0
        for prod, data in product_stock.items():
            quantity = input[f"quant_{prod}"]()
            total += quantity * data["preco"]
        return total

    @output
    @render.text
    def total_value():
        return f"Total da compra: R${total_value_calc():.2f}"
    

    previous_click = {"value": 0}  # Estado simples para armazenar o valor anterior

    @reactive.effect
    def finalize():
        current_click = input.finalize_purchase()
        
        # Verifica se o botão foi clicado novamente (impede reexecução após reset dos inputs)
        if current_click > previous_click["value"]:
            previous_click["value"] = current_click  # Atualiza o clique anterior
            total = total_value_calc()  # Calcula o total da compra
            quantities_to_update = {}  # Dicionário para armazenar os produtos válidos

            # Verifica se as quantidades solicitadas são válidas
            for prod, data in product_stock.items():
                quantity = input[f"quant_{prod}"]()
                if quantity > data["quantidade"]:
                    # Mostra erro se a quantidade for maior que o estoque disponível
                    ui.notification_show(f"Sinto muito, quantidade de {prod} indisponível.", duration=3)
                    
                    # Reseta os inputs para os produtos válidos já selecionados
                    for prod in quantities_to_update.keys():
                        session.send_input_message(f"quant_{prod}", {"value": 0})
                    return  # Interrompe a execução

                if quantity > 0:
                    quantities_to_update[prod] = quantity  # Armazena produto e quantidade válidos

            # Atualiza o estoque subtraindo as quantidades compradas
            for prod, quantity in quantities_to_update.items():
                product_stock[prod]["quantidade"] -= quantity

            # Exibe a notificação de sucesso da compra
            ui.notification_show(f"Compra finalizada. Total: R${total:.2f}", duration=5)

            # Reseta os inputs para zero após a compra
            for prod in quantities_to_update.keys():
                session.send_input_message(f"quant_{prod}", {"value": 0})

            
            

           
            

# Executa o app
app = App(app_ui, server)
