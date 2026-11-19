from raincloud.scripts.userinterface import Button, Menu, Matrix


def resume(app):
	app.close_menu()


def quit_game(app):
	app.running = False


def open_settings(app):
	app.open_menu("settings")


def filled_matrix(width, height) -> Matrix:
	return tuple(tuple(1 for _ in range(width)) for _ in range(height))


MENUS = {
	"pause": Menu(
		title="Paused",
		matrix=filled_matrix(13, 16),
		corner_type="rounded",
		edge_style="straight",
		colors=(
			(255, 255, 255, 0),
			(0, 192, 192, 255),
			(0, 192, 192, 255),
			(0, 255, 255, 255),
			(0, 255, 255, 255),
			(0, 255, 255, 255),
			(0, 128, 128, 128),
			(0, 128, 128, 128),
		),
		buttons=(
			Button(label="Return", action=resume),
			Button(label="Settings", action=open_settings),
			Button(label="Quit", action=quit_game),
		),
	),
	"settings": None,  # Filled in by settings module at runtime
}
