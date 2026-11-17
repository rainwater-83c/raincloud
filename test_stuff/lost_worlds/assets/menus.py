from raincloud.scripts.userinterface import Button, Menu, Matrix


def resume(app):
	app.close_menu()


def quit_game(app):
	app.running = False


def filled_matrix(width, height) -> Matrix:
	return tuple(tuple(1 for _ in range(width)) for _ in range(height))


MENUS = {
	"pause": Menu(
		title="Paused",
		matrix=filled_matrix(13, 12),
		corner_type="rounded",
		edge_style="straight",
		colors=(
			(15, 20, 32, 235),
			(22, 30, 45, 235),
			(31, 44, 62, 235),
			(48, 65, 84, 235),
			(76, 96, 114, 235),
			(111, 132, 148, 235),
			(157, 176, 190, 235),
			(213, 225, 233, 235),
		),
		buttons=(
			Button(label="Resume", action=resume),
			Button(label="Quit", action=quit_game),
		),
	),
}
