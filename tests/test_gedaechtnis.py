"""Vorwissensanalyse: Lesen des Claude-Gedächtnisses."""
from kern.gedaechtnis import als_markdown, relevante


def mem(ordner, name, typ, text, beschreibung=""):
    ordner.mkdir(parents=True, exist_ok=True)
    (ordner / f"{name}.md").write_text(
        f"---\nname: {name}\ndescription: \"{beschreibung}\"\nmetadata:\n  type: {typ}\n---\n\n{text}\n")


def test_liest_person_immer_und_projekte_nach_thema(repo, tmp_path):
    projekte = tmp_path / "home" / "projects"
    mem(projekte / "-home-j-Documents-uni" / "memory", "studium", "user", "Werkstudent 20 h/Woche, Cyber Security.")
    mem(projekte / "-home-j-Work-os-praktikum" / "memory", "scheduler", "project", "Hat einen CFS-Scheduler nachgebaut.")
    mem(projekte / "-home-j-Work-homelab" / "memory", "docker", "project", "Docker-Compose für Jellyfin.")
    mem(projekte / "-home-j-Documents-gesundheit" / "memory", "schulter", "user", "MRT Schulter links.")
    (projekte / "-home-j-Documents-uni" / "memory" / "MEMORY.md").write_text("- index")
    (repo / "ariadne.toml").write_text(
        f'[gedaechtnis]\nquellen = ["{projekte}/*/memory/*.md"]\nausschliessen = ["*gesundheit*"]\nimmer = ["user"]\n')

    immer, passend = relevante(["Scheduler"])
    assert [e["name"] for e in immer] == ["studium"]
    assert [e["name"] for e in passend] == ["scheduler"]
    assert immer[0]["projekt"] == "Documents-uni"

    md = als_markdown(["Scheduler"])
    assert "Hypothese" in md and "CFS-Scheduler" in md and "Jellyfin" not in md and "Schulter" not in md
