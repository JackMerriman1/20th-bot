async def message_test(interaction, client):
    """Starts a DM with the user and asks them to type 'yes' or 'no'."""
    try:
        await interaction.user.send("Hello! Please type 'yes' or 'no'.")

        def check(message):
            return message.author == interaction.user and message.content.lower() in ["yes", "no"]

        response = await client.wait_for("message", check=check, timeout=30)  # Wait for user response
        
        if response.content.lower() == "yes":
            await interaction.user.send("You chose YES!")
        else:
            await interaction.user.send("You chose NO!")
    except discord.Forbidden:
        await interaction.send("I can't send you a DM. Please check your settings.")
    except discord.TimeoutError:
        await interaction.user.send("You took too long to respond!")

from discord.ui import Select, View
import discord

# print(help(Select))

async def select_test(interaction, client):
    
    select_options = [("A", "Letter A"), ("B", "Letter B"), ("C", "Letter C")]
    options = [discord.SelectOption(label=option[0], description=option[1]) for option in select_options]

    select = Select(placeholder="Select an option",
                    max_values=len(select_options),
                    options=options)
    
    view = View()
    view.add_item(select)

    # print(help(interaction.response.send_message))
    await interaction.response.send_message(content="Select a letter", view=view)
    return
