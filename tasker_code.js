var question = prompt("Que puis-je faire pour toi ?");

if (question && question.trim() !== "") {
    // Remplacez VOTRE_IP_VPS et VOTRE_CLE_SECRETE par vos propres valeurs
    var host = "VOTRE_IP_VPS:8000";
    var secretKey = "VOTRE_CLE_SECRETE";
    var url = "http://" + host + "/api/tasker/command?q=" + encodeURIComponent(question) + "&key=" + encodeURIComponent(secretKey);
    
    var xhttp = new XMLHttpRequest();
    xhttp.open("GET", url, false);
    xhttp.send();

    if (xhttp.status == 200) {
        var data = JSON.parse(xhttp.responseText);

        // Déclenchement automatique de l'horloge Android
        if (data.action === "timer" && data.seconds > 0) {
            sendIntent(
                "android.intent.action.SET_TIMER",
                "Activity",
                "",
                "",
                "",
                "",
                [
                    "android.intent.extra.alarm.LENGTH:" + data.seconds,
                    "android.intent.extra.alarm.MESSAGE:" + data.label,
                    "android.intent.extra.alarm.SKIP_UI:true"
                ],
                []
            );
        }

        // Réponse vocale avec le moteur vocal par défaut du téléphone
        if (data.reply) {
            say(data.reply);
        }
    } else {
        flash("Erreur connexion Hercul VPS");
    }
}
