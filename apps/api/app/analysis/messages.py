"""Textos del motor de reglas.

Cada regla tiene varias redacciones equivalentes. La variante se elige con un
hash de ``match_id + rule_id``: dos partidas distintas leen mensajes distintos,
pero la misma partida siempre genera el mismo texto. Asi el demo y los tests
siguen siendo deterministas sin depender de ``random``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .rules import Finding


@dataclass(frozen=True)
class Copy:
    title: str
    detail: str
    recommendation: str


LABELS: dict[str, str] = {
    "first_death_rate": "Regalas primeros contactos",
    "untraded_deaths": "Muertes sin tradear",
    "attack_no_utility": "Ataque sin utilidad",
    "force_buy_after_loss": "Fuerzas tras perder",
    "buy_without_armor": "Compras sin armadura",
    "low_kast": "KAST bajo",
    "low_headshot_pct": "Puntería a la cabeza",
    "low_adr": "Daño por ronda bajo",
    "weak_attack_side": "Ataque débil",
    "weak_defense_side": "Defensa débil",
    "low_individual_impact": "Impacto individual bajo",
    "first_death_attack": "Primeros contactos al atacar",
    "death_without_damage": "Muertes sin daño",
    "clutch_failures": "1vX sin cerrar",
    "late_deaths": "Muertes tardías",
    "force_buy_ineffective": "Fuerzas sin premio",
    "full_buy_bleed": "Full buys perdidos",
    "half_buys": "Compras a medias",
    "anti_eco_letdown": "Anti-eco regalada",
    "defense_no_utility": "Defensa sin utilidad",
    "ult_hoarding": "Definitiva guardada",
    "lost_carry_rounds": "Rondas grandes perdidas",
    "irregular_form": "Forma irregular",
    "adr_drop_in_losses": "Daño que cae al perder",
    "pistol_weak": "Pistolas perdidas",
    "attack_timeouts": "Ataques sin plantar",
    "second_half_drop": "Segunda mitad floja",
}


CATALOG: dict[str, tuple[Copy, ...]] = {
    "first_death_rate": (
        Copy(
            "Regalas demasiados primeros contactos",
            "Moriste en el primer contacto en {count} de {total} rondas ({rate:.0f}%). "
            "Cada 4v5 temprano cuesta la ronda.",
            "Juega 3 partidas sin ser el primero en asomarte: deja que un compañero "
            "abra el duelo o gana información con una habilidad.",
        ),
        Copy(
            "Eres el primer muerto demasiadas veces",
            "En {count} de {total} rondas ({rate:.0f}%) tu muerte fue la primera de la ronda. "
            "El equipo empieza cada pelea en desventaja.",
            "Antes de asomarte pide un flash o un dron. Si nadie abre, no entres primero.",
        ),
        Copy(
            "Tu primer contacto se pierde",
            "{count} primeras muertes en {total} rondas ({rate:.0f}%). Estás regalando "
            "la ventaja numérica antes de que empiece la pelea.",
            "Cambia el orden: utilidad primero, compañero de entrada segundo, tú de trade. "
            "Nunca solo.",
        ),
    ),
    "untraded_deaths": (
        Copy(
            "Tus muertes no se están tradeando",
            "Solo el {trade:.0f}% de tus muertes fueron tradeadas. {count} quedaron sin "
            "respuesta de un compañero.",
            "Acuerda con tu dúo una regla simple: si uno entra, el otro está a menos de "
            "5 segundos para tradearte.",
        ),
        Copy(
            "Mueres solo y sin castigo",
            "El {trade:.0f}% de tus muertes tuvo trade. {count} veces nadie cobró tu duelo.",
            "Juega en pareja y no abras sin cobertura. Si entras solo, espera el trade "
            "antes de comprometerte.",
        ),
        Copy(
            "Te matan y nadie responde",
            "{count} muertes sin trade y un trade rate del {trade:.0f}%. Estás dando "
            "ventaja gratis.",
            "Pacta una regla: el segundo jugador entra cuando el primero recibe daño, "
            "no cuando ya murió.",
        ),
    ),
    "attack_no_utility": (
        Copy(
            "Estás entrando sin utilidad",
            "En {zero} de {known} rondas de ataque con compra usaste cero habilidades. "
            "Entrar sin humo, flash o info regala los duelos.",
            "Antes de cada ataque define qué habilidad abre la entrada y úsala en los "
            "primeros 20 segundos. Si no la usas, no la compres.",
        ),
        Copy(
            "Atacas sin gastar habilidades",
            "{zero} de {known} ataques con compra terminaron con 0 usos de utilidad.",
            "Si compras una habilidad, úsala. Si no vas a usarla, ahorra ese dinero para "
            "el rifle.",
        ),
        Copy(
            "Tu entrada es a cara de perro",
            "Cero utilidad usada en {zero} de {known} ataques con compra. Dependes solo "
            "de ganar el duelo seco.",
            "Entra con humo o flash propia. Una habilidad bien puesta vale más que un "
            "primer disparo.",
        ),
    ),
    "force_buy_after_loss": (
        Copy(
            "Fuerzas compras tras perder la ronda",
            "Forzaste la compra {count} veces después de una ronda perdida. Eso rompe la "
            "economía para las rondas siguientes.",
            "Define dos reglas de compra: full buy desde 3.900 créditos y save por debajo "
            "de 2.000. En el save compra solo pistola y armadura ligera.",
        ),
        Copy(
            "Rompes la economía forzando",
            "{count} fuerzas después de una derrota. Estás hipotecando las dos rondas "
            "siguientes.",
            "Tras perder, revisa los créditos del equipo antes de comprar. Si no llegas a "
            "3.900, save.",
        ),
        Copy(
            "Compras en tilt después de perder",
            "Forzaste {count} veces la ronda siguiente a una derrota.",
            "Pon una regla física: después de perder, compra solo pistola y armadura "
            "ligera hasta el full buy.",
        ),
    ),
    "buy_without_armor": (
        Copy(
            "Compras arma sin armadura",
            "En {count} rondas compraste un arma cara sin armadura. Un disparo a la cabeza "
            "o dos al cuerpo te dejan fuera.",
            "Si compras rifle, compra siempre armadura completa. Si no llega, baja a "
            "Spectre + armadura antes que Vandal sin chaleco.",
        ),
        Copy(
            "Vas al duelo sin chaleco",
            "Arma de más de 2.000 créditos sin armadura en {count} rondas.",
            "La armadura gana duelos. Antes de subir de arma, asegura el chaleco completo.",
        ),
        Copy(
            "Ahorras en la pieza equivocada",
            "{count} compras caras sin armadura. Estás ahorrando justo donde no se puede.",
            "Compra armadura con el rifle y recorta en utilidad o en el arma, nunca en el "
            "chaleco.",
        ),
    ),
    "low_kast": (
        Copy(
            "Poco impacto por ronda",
            "Tu KAST es {kast:.0f}% (referencia sana: 70%+). En demasiadas rondas no "
            "aportas kill, asistencia, supervivencia ni trade.",
            "Prioriza sobrevivir y tradeear antes que buscar kills aisladas. Revisa tus "
            "3 muertes más tempranas y evita repetir esa posición.",
        ),
        Copy(
            "Demasiadas rondas en blanco",
            "Solo aportaste en el {kast:.0f}% de las rondas. El resto fueron rondas sin "
            "kill, asistencia, trade ni supervivencia.",
            "Juega más cerca del equipo: asiste, cubre y sobrevive. El KAST sube sin "
            "necesidad de buscar más kills.",
        ),
        Copy(
            "Desapareces en muchas rondas",
            "KAST del {kast:.0f}%. Hay rondas donde no dejas nada para la ronda.",
            "Cada ronda necesita una acción tuya: daño, cobertura, utilidad o trade. Elige "
            "una y ejecútala.",
        ),
    ),
    "low_headshot_pct": (
        Copy(
            "Poco porcentaje de headshots",
            "Tu HS% es {hs:.1f}%. Estás ganando duelos por volumen de daño y no por "
            "precisión.",
            "10 minutos de Aim Lab o rango de tiro antes de jugar: fija la mira a altura "
            "de cabeza y haz flicks cortos.",
        ),
        Copy(
            "La mira está baja",
            "HS% del {hs:.1f}%: estás disparando al cuerpo más de lo necesario.",
            "Haz deathmatch con una sola regla: no dispares hasta tener la mira a altura "
            "de cabeza.",
        ),
        Copy(
            "Duelos ganados a base de balas",
            "Solo el {hs:.1f}% de tus impactos son a la cabeza. Necesitas más balas de "
            "las que deberías para cerrar un duelo.",
            "Calienta con 100 kills de cabeza en rango de tiro y mantén la cruz a altura "
            "de hombro.",
        ),
    ),
    "low_adr": (
        Copy(
            "Daño por ronda bajo",
            "Tu ADR es {adr:.0f}. Por debajo de 120 suele indicar que llegas tarde a los "
            "duelos o que mueres sin intercambiar daño.",
            "Juega más cerca de tu equipo y participa con daño previo: una flash o un "
            "disparo de cobertura antes de entrar.",
        ),
        Copy(
            "No estás dejando daño",
            "ADR de {adr:.0f}: el rival sale de las peleas con demasiada vida.",
            "Acompaña la entrada y dispara antes de morir. Un trade vale más que un kill "
            "limpio.",
        ),
        Copy(
            "Llegas tarde a los duelos",
            "{adr:.0f} de ADR. Estás entrando cuando la pelea ya se resolvió.",
            "Anticípate al contacto: preaim, utilidad de entrada y dispara en cuanto veas "
            "el primer cuerpo.",
        ),
    ),
    "weak_attack_side": (
        Copy(
            "Tu ataque es el lado débil",
            "Ganas el {rate:.0f}% de tus rondas de ataque ({rounds} rondas). El problema no "
            "es el aim, es la ejecución de entrada.",
            "Elige un sitio por ronda, usa utilidad para cortar la retaguardia y entra "
            "todos juntos. Prohibido entrar de uno en uno.",
        ),
        Copy(
            "No cierras los ataques",
            "Winrate de ataque del {rate:.0f}% en {rounds} rondas.",
            "Fija un plan A y un plan B antes de comprar. Si no hay información, no entres "
            "de uno en uno.",
        ),
        Copy(
            "El ataque se te cae",
            "Solo {rate:.0f}% de ataques ganados ({rounds} jugados).",
            "Entra con tu equipo y asegura el post-plant. Ganar el sitio no sirve si no lo "
            "cubres.",
        ),
    ),
    "weak_defense_side": (
        Copy(
            "Tu defensa es el lado débil",
            "Ganas el {rate:.0f}% de tus rondas de defensa ({rounds} rondas). Estás "
            "regalando el mapa en el lado defensivo.",
            "No repitas la misma posición dos rondas seguidas. Juega retrasado con "
            "compañero y pide información antes de rotar.",
        ),
        Copy(
            "Te abren el mapa en defensa",
            "Winrate defensivo del {rate:.0f}% en {rounds} rondas.",
            "Juega retrasado con compañero y cambia de ángulo. No regales el primer "
            "contacto.",
        ),
        Copy(
            "Defensa sin ajustes",
            "{rate:.0f}% de rondas defensivas ganadas ({rounds}).",
            "Después de cada ronda perdida cambia de posición. Si insistes en el mismo "
            "sitio, te leen.",
        ),
    ),
    "low_individual_impact": (
        Copy(
            "Impacto individual bajo",
            "Promedias {kpr:.2f} kills por ronda y solo abres el marcador en el "
            "{fb:.0f}% de las rondas. Estás jugando demasiado pasivo.",
            "En defensa, toma una posición agresiva con salida segura y busca un primer "
            "contacto por ronda. En ataque, acompaña la entrada con daño.",
        ),
        Copy(
            "Juegas demasiado pasivo",
            "{kpr:.2f} KPR y {fb:.0f}% de primeros contactos ganados.",
            "Busca un primer contacto por ronda con salida segura. No esperes a que el "
            "equipo haga todo el trabajo.",
        ),
        Copy(
            "Te falta presencia en la pelea",
            "Solo {kpr:.2f} kills por ronda y {fb:.0f}% de aperturas ganadas.",
            "Cada ronda debe tener un plan para tu primera pelea. Elige ángulo, pide "
            "utilidad y compite.",
        ),
    ),
    # --- Nuevas reglas -----------------------------------------------------
    "first_death_attack": (
        Copy(
            "Mueres primero al entrar",
            "Fuiste el primer muerto en {count} de {rounds} ataques ({rate:.0f}%).",
            "Deja que abra otro o entra con utilidad. Tú entras segundo para tradeear.",
        ),
        Copy(
            "Tu entrada es la primera en caer",
            "{count} primeros contactos perdidos en {rounds} rondas de ataque "
            "({rate:.0f}%).",
            "No seas la punta de lanza sin información. Pide flash o dron antes de cruzar.",
        ),
        Copy(
            "El ataque empieza con tu muerte",
            "Primer muerto en {count} de {rounds} ataques ({rate:.0f}%). El equipo entra "
            "en 4v5 casi cada ronda.",
            "Cambia el rol de entrada: juega de segundo y cobra el trade del que abre.",
        ),
    ),
    "death_without_damage": (
        Copy(
            "Mueres sin dejar daño",
            "Promedias {damage_per_death:.0f} de daño por muerte en {deaths} muertes.",
            "Antes de morir, dispara o suelta una habilidad. Un 20 de daño extra cambia "
            "el trade.",
        ),
        Copy(
            "Tus muertes son baratas",
            "Solo {damage_per_death:.0f} de daño por muerte ({deaths} muertes).",
            "Entra con un compañero y asegura al menos un disparo antes de caer.",
        ),
        Copy(
            "Regalas la vida sin intercambio",
            "{damage_per_death:.0f} de daño medio por muerte. El rival gana el duelo casi "
            "gratis.",
            "Si vas a perder el duelo, retrocede y obliga al rival a gastar balas o "
            "utilidad.",
        ),
    ),
    "clutch_failures": (
        Copy(
            "No cierras los 1vX",
            "Ganaste {wins} de {attempts} situaciones de clutch ({rate:.0f}%).",
            "En 1vX juega el tiempo, separa a los rivales y usa la utilidad antes de "
            "disparar.",
        ),
        Copy(
            "Los 1vX se te escapan",
            "{wins} clutches ganados de {attempts} ({rate:.0f}%).",
            "No corras hacia el primero que veas: espera el sonido o el segundo contacto.",
        ),
        Copy(
            "Te falta cerrar las rondas solo",
            "Tasa de clutch del {rate:.0f}% en {attempts} intentos.",
            "Entrena 1v1 y 2v1 en rango con la regla de no recargar en campo abierto.",
        ),
    ),
    "late_deaths": (
        Copy(
            "Mueres cuando la ronda ya está decidida",
            "{count} de tus {deaths} muertes llegaron después del primer minuto.",
            "Si la ronda está perdida, guarda la vida y el arma. Una muerte tardía no "
            "aporta.",
        ),
        Copy(
            "Muertes que no cambian nada",
            "{count} muertes pasados los 60 segundos de ronda.",
            "Aprende a reconocer la ronda perdida y retírate para el save.",
        ),
        Copy(
            "Pagas el precio tarde",
            "{count} de {deaths} muertes fueron en la segunda mitad de la ronda.",
            "Rotar tarde y sin información cuesta caro. Si no hay tiempo, no entres.",
        ),
    ),
    "force_buy_ineffective": (
        Copy(
            "Tus fuerzas no están funcionando",
            "Ganaste {wins} de {rounds} fuerzas ({rate:.0f}%).",
            "Si la fuerza no gana, no la hagas: save y vuelve con full buy.",
        ),
        Copy(
            "Forzar no te da la ronda",
            "{rate:.0f}% de winrate en {rounds} compras forzadas.",
            "Cambia la regla: fuerza solo en 2v1 económico o en la última ronda de la "
            "mitad.",
        ),
        Copy(
            "Fuerzas por inercia",
            "Solo {wins} victorias en {rounds} rondas forzadas.",
            "Antes de forzar, cuenta los créditos del equipo. Si no hay ventaja, no hay "
            "fuerza.",
        ),
    ),
    "full_buy_bleed": (
        Copy(
            "Pierdes las rondas de full buy",
            "Ganaste {wins} de {rounds} full buys ({rate:.0f}%).",
            "Revisa la ejecución: si tienes armas y pierdes, el problema es el plan de "
            "ronda.",
        ),
        Copy(
            "No conviertes la ventaja de armas",
            "{rate:.0f}% de winrate en {rounds} rondas de compra completa.",
            "Elige un plan simple y ejecútalo con el equipo. No cambies de sitio a mitad "
            "de ronda.",
        ),
        Copy(
            "El full buy no te alcanza",
            "{wins} de {rounds} full buys ganados.",
            "Gasta la utilidad en la entrada y evita duelos aislados. Con armas, la ronda "
            "se juega en equipo.",
        ),
    ),
    "half_buys": (
        Copy(
            "Compras a medias",
            "{count} rondas de save en las que gastaste 1.500 créditos o más.",
            "En save compra pistola y armadura ligera. No mezcles save con compra cara.",
        ),
        Copy(
            "Ni save ni full buy",
            "{count} compras intermedias que rompen la economía.",
            "Define tres niveles: full, force y save. Cualquier otra cosa es dinero "
            "perdido.",
        ),
        Copy(
            "Tus saves no ahorran",
            "{count} saves con más de 1.500 créditos gastados.",
            "Si vas a guardar, guarda de verdad. Si vas a comprar, compra para ganar.",
        ),
    ),
    "anti_eco_letdown": (
        Copy(
            "Regalas la anti-eco",
            "Perdiste {count} de {rounds} rondas después de ganar la pistola.",
            "En anti-eco juega junto y no regales duelos largos. La ventaja de armas no "
            "perdona.",
        ),
        Copy(
            "La ronda después de la pistola se cae",
            "{count} derrotas en anti-eco de {rounds} rondas.",
            "Tras ganar la pistola, compra y juega seguro: agrupa, cubre y obliga al rival "
            "a entrar.",
        ),
        Copy(
            "Tiras la ventaja de la pistola",
            "{count} anti-ecos perdidas. Estás devolviendo la ventaja que ganaste.",
            "No caces kills en anti-eco. Mantén la posición, cubre los flancos y deja que "
            "el rival entre.",
        ),
    ),
    "defense_no_utility": (
        Copy(
            "Defiendes sin gastar utilidad",
            "En {zero} de {known} rondas de defensa con compra no usaste ninguna "
            "habilidad.",
            "Usa la utilidad para retrasar la entrada, no para después de perder el sitio.",
        ),
        Copy(
            "Tu defensa es solo aim",
            "Cero usos de utilidad en {zero} de {known} defensas.",
            "Suelta una habilidad al inicio de la ronda: información, humo o trampa. "
            "Defiende con tiempo.",
        ),
        Copy(
            "Guardas la utilidad en defensa",
            "{zero} de {known} rondas defensivas sin habilidad usada.",
            "Una utilidad bien puesta compra 5 segundos. Esos segundos ganan rondas.",
        ),
    ),
    "ult_hoarding": (
        Copy(
            "Guardas la definitiva",
            "Usaste la ulti en el {usage:.0f}% de {rounds} rondas.",
            "La definitiva gana rondas, no se guarda. Úsala en la primera ronda donde "
            "cambie el marcador.",
        ),
        Copy(
            "La ulti se queda en el bolsillo",
            "{usage:.0f}% de uso en {rounds} rondas.",
            "Si tienes ulti y la ronda es clave, suéltala. Recargarla es más fácil que "
            "remontar.",
        ),
        Copy(
            "Miedo a gastar la definitiva",
            "Solo la usaste en {usage:.0f}% de las rondas.",
            "Define una situación concreta para tu ulti y úsala en cuanto se dé.",
        ),
    ),
    "lost_carry_rounds": (
        Copy(
            "Tiras las rondas donde cargas",
            "Perdiste {count} rondas en las que ya habías hecho 3+ kills o 200+ de daño.",
            "Cuando estás arriba, juega el tiempo y no regales el 1vX. Cierra la ronda "
            "con el equipo.",
        ),
        Copy(
            "Tus rondas grandes no se convierten",
            "{count} rondas perdidas después de un gran impacto individual.",
            "Después de una buena entrada, cambia a modo seguro: cubre, recarga y espera "
            "el apoyo.",
        ),
        Copy(
            "El esfuerzo no se traduce en rondas",
            "{count} rondas grandes que acabaron en derrota.",
            "Revisa esas rondas: seguramente sobre-extendiste después de la primera kill.",
        ),
    ),
    "irregular_form": (
        Copy(
            "Tu forma es una montaña rusa",
            "La variación de daño entre rondas es del {cv:.0f}%: pasas de {worst} a "
            "{best} de daño.",
            "Calienta igual antes de cada partida y juega un plan estable. La regularidad "
            "gana más que el pico.",
        ),
        Copy(
            "Rondas muy buenas y rondas invisibles",
            "Coeficiente de variación del {cv:.0f}% en daño por ronda (de {worst} a "
            "{best}).",
            "Reduce el rango: mismo rol, mismas posiciones y una rutina de calentamiento "
            "fija.",
        ),
        Copy(
            "Impacto intermitente",
            "Tu daño por ronda oscila un {cv:.0f}% entre rondas.",
            "No cambies de estilo cada ronda. Elige un plan y ejecútalo aunque vaya mal.",
        ),
    ),
    "adr_drop_in_losses": (
        Copy(
            "Tus derrotas son demasiado baratas",
            "En las derrotas haces {adr_loss:.0f} de ADR, frente a {adr_win:.0f} en las "
            "victorias ({losses} derrotas).",
            "Cuando el equipo va abajo, no desaparezcas: juega retrasado, tradea y busca "
            "daño seguro.",
        ),
        Copy(
            "Bajas los brazos cuando pierdes",
            "{adr_loss:.0f} ADR en derrotas y {adr_win:.0f} en victorias.",
            "Mantén el mismo plan incluso en rondas perdidas. El daño de una ronda "
            "perdida también cuenta.",
        ),
        Copy(
            "Solo apareces cuando ganas",
            "Diferencia de {adr_win:.0f} a {adr_loss:.0f} de ADR entre victorias y "
            "derrotas.",
            "En las rondas cuesta arriba, busca un duelo con salida y deja daño antes de "
            "caer.",
        ),
    ),
    "pistol_weak": (
        Copy(
            "Pierdes las pistolas",
            "Ganaste {wins} de {rounds} rondas de pistola.",
            "Practica la pistola: compra armadura ligera, juega en grupo y evita duelos "
            "largos.",
        ),
        Copy(
            "Las rondas de pistola se escapan",
            "{wins} victorias en {rounds} pistolas.",
            "En pistola, la utilidad y el número ganan. Entra con el equipo y cubre el "
            "trade.",
        ),
        Copy(
            "Empiezas cada mitad cuesta abajo",
            "Solo {wins} de {rounds} pistolas ganadas.",
            "Calienta la pistola antes de la partida y juega el primer contacto con "
            "cobertura.",
        ),
    ),
    "attack_timeouts": (
        Copy(
            "No llegas a plantar",
            "Perdiste {count} de {rounds} ataques por tiempo.",
            "Define un timing: entra a los 60 segundos, planta y cubre. El tiempo también "
            "es un recurso.",
        ),
        Copy(
            "El ataque muere por reloj",
            "{count} rondas de ataque perdidas por tiempo.",
            "Asigna un líder de ronda y fija una hora de entrada. No esperes a que queden "
            "15 segundos.",
        ),
        Copy(
            "Te come el reloj en ataque",
            "{count} ataques terminados por time expired.",
            "Si no hay información, entra igual con el equipo. Una entrada imperfecta es "
            "mejor que no plantar.",
        ),
    ),
    "second_half_drop": (
        Copy(
            "Se te cae la segunda mitad",
            "Ganas el {first_rate:.0f}% de la primera mitad y solo el {second_rate:.0f}% "
            "de la segunda.",
            "Ajusta el plan al cambiar de lado: no repitas lo que funcionó en la primera "
            "mitad.",
        ),
        Copy(
            "Vuelves del descanso peor",
            "Primera mitad {first_rate:.0f}%, segunda {second_rate:.0f}%.",
            "Usa el descanso para cambiar una posición y una regla de compra. No juegues "
            "en piloto automático.",
        ),
        Copy(
            "La segunda mitad te pasa por encima",
            "Caída de {first_rate:.0f}% a {second_rate:.0f}% después del cambio de lado.",
            "Revisa las primeras dos rondas del segundo lado y cambia el ángulo que te "
            "están leyendo.",
        ),
    ),
}


FINDINGS_SUMMARIES: tuple[str, ...] = (
    "{result} {us}-{them} en {map} con {agent}. {kda}, {acs:.0f} ACS y {kast:.0f}% "
    "KAST. {strength_text} El foco de la partida: {focus}.",
    "Cierras {us}-{them} en {map} con {agent}. {kda}, {acs:.0f} ACS y {kast:.0f}% "
    "KAST. {strength_text} Lo más repetido: {focus}.",
    "{map}, {us}-{them} con {agent}: {kda}, {acs:.0f} ACS y {kast:.0f}% KAST. "
    "{strength_text} La prioridad número uno: {focus}.",
)

CLEAN_SUMMARIES: tuple[str, ...] = (
    "{result} {us}-{them} en {map} con {agent}. {kda}, {acs:.0f} ACS y "
    "{kast:.0f}% KAST. {strength_text} No hay errores graves repetidos: mantén esta "
    "base y sube la dificultad de los duelos que eliges.",
    "{result} {us}-{them} en {map} con {agent}. {kda}, {acs:.0f} ACS y "
    "{kast:.0f}% KAST. {strength_text} Sin patrones de error claros: repite lo que "
    "funcionó y añade una variable por partida.",
    "{result} {us}-{them} en {map} con {agent}. {kda}, {acs:.0f} ACS y "
    "{kast:.0f}% KAST. {strength_text} Ningún fallo se repite lo suficiente para "
    "corregirlo: consolida el nivel antes de cambiar de agente.",
)


DRILL_POOL: dict[str, tuple[str, ...]] = {
    "Duelos": (
        "10 minutos de deathmatch buscando solo primeros contactos con salida segura.",
        "Graba una partida y anota las 3 primeras muertes: dónde estabas y quién te cubría.",
        "Juega 3 partidas como segundo de entrada y cobra el trade de tu compañero.",
        "Practica 1v1 en rango con la regla de no recargar en campo abierto.",
    ),
    "Economía": (
        "Antes de cada compra di en voz alta el nivel: full, force o save.",
        "Una partida entera sin forzar después de perder: solo save o full buy.",
        "Anota los créditos del equipo al final de cada ronda durante una partida.",
        "Juega 5 rondas de save comprando solo pistola y armadura ligera.",
    ),
    "Utilidad": (
        "Antes de cada ataque elige la habilidad que abre y dila en voz alta.",
        "Una partida usando utilidad en los primeros 20 segundos de cada ataque.",
        "Cuenta cuántas rondas usas la definitiva y ponte un mínimo de 3.",
        "Practica una entrada con humo + flash en rango antes de jugar.",
    ),
    "Impacto": (
        "10 minutos de rango de tiro con foco en daño por ronda, no en kills.",
        "Revisa tus 3 rondas con menos daño y anota por qué no participaste.",
        "Juega una partida midiendo KAST: aporta algo en cada ronda.",
        "En defensa, elige una posición agresiva con ruta de salida segura.",
    ),
    "Aim": (
        "10 minutos de Aim Lab o rango de tiro con la mira a altura de cabeza.",
        "Deathmatch con una sola regla: no dispares hasta tener la cruz en la cabeza.",
        "100 kills de cabeza en rango de tiro antes de la primera partida.",
        "Calienta 5 minutos de flicks cortos y microajustes, sin barridos largos.",
    ),
    "Lados": (
        "Antes de cambiar de lado elige una posición nueva para la segunda mitad.",
        "Una partida con un plan de ronda escrito para ataque y otro para defensa.",
        "En ataque, fija una hora de entrada y respétala durante 5 rondas.",
        "En defensa, cambia de ángulo después de cada ronda perdida.",
    ),
}

CLEAN_DRILLS: tuple[str, ...] = (
    "Revisa una ronda perdida por partida y anota por qué la perdiste.",
    "Mantén la misma rutina de calentamiento antes de jugar.",
    "Elige una métrica por semana y mide si sube en tus últimas 5 partidas.",
    "Cambia una sola variable por partida para saber qué te está funcionando.",
)


def pick_index(match_id: str, key: str, size: int) -> int:
    digest = hashlib.sha256(f"{match_id}|{key}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % max(1, size)


def pick_text(match_id: str, key: str, options: tuple[str, ...]) -> str:
    return options[pick_index(match_id, key, len(options))]


def render(rule_id: str, match_id: str, context: dict) -> Copy:
    variants = CATALOG[rule_id]
    copy = variants[pick_index(match_id, rule_id, len(variants))]
    return Copy(
        title=copy.title.format(**context),
        detail=copy.detail.format(**context),
        recommendation=copy.recommendation.format(**context),
    )


def label(rule_id: str) -> str:
    return LABELS.get(rule_id, rule_id)


def drills_for(findings: list[Finding], match_id: str) -> list[str]:
    result: list[str] = []
    for finding in findings:
        pool = DRILL_POOL.get(finding.category)
        if not pool:
            continue
        start = pick_index(match_id, f"drill|{finding.rule_id}", len(pool))
        for offset in range(len(pool)):
            candidate = pool[(start + offset) % len(pool)]
            if candidate not in result:
                result.append(candidate)
                break
        if len(result) == 3:
            break
    for candidate in CLEAN_DRILLS:
        if len(result) == 3:
            break
        if candidate not in result:
            result.append(candidate)
    return result[:3]
