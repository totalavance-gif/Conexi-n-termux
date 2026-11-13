package com.nexos.musecontrol

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MuseControlApp()
        }
    }
}

private const val SERVER_URL = "http://127.0.0.1:8080/run"

/** Manda token + comando al servidor local. Devuelve (exito, mensaje). */
private suspend fun postRun(token: String, command: String): Pair<Boolean, String> =
    withContext(Dispatchers.IO) {
        try {
            val conn = (URL(SERVER_URL).openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 8000
                readTimeout = 8000
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
            val body = JSONObject()
                .put("token", token)
                .put("command", command)
                .toString()
            conn.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
            val code = conn.responseCode
            val stream = if (code in 200..299) conn.inputStream else conn.errorStream
            val text = stream?.bufferedReader()?.readText() ?: ""
            conn.disconnect()
            (code in 200..299) to "HTTP $code · $text"
        } catch (e: Exception) {
            false to "Sin conexión: ${e.message ?: "revisa que el servidor esté corriendo"}"
        }
    }

@Composable
fun MuseControlApp() {
    var token by remember { mutableStateOf(BuildConfig.DEFAULT_TOKEN) }
    var status by remember { mutableStateOf("Listo. Arranca el servidor primero.") }
    var lastOk by remember { mutableStateOf<Boolean?>(null) }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    fun send(command: String) {
        if (busy) return
        busy = true
        status = "Enviando \"$command\"…"
        lastOk = null
        scope.launch {
            val (ok, message) = postRun(token, command)
            status = if (ok) "OK · $message" else "ERROR · $message"
            lastOk = ok
            busy = false
        }
    }

    MaterialTheme(colorScheme = darkColorScheme()) {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = MaterialTheme.colorScheme.background
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(24.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Text(
                    "Muse Control",
                    fontSize = 28.sp,
                    fontWeight = FontWeight.Bold
                )
                OutlinedTextField(
                    value = token,
                    onValueChange = { token = it },
                    label = { Text("Token secreto") },
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                    modifier = Modifier.fillMaxWidth()
                )
                Button(
                    onClick = { send("muse") },
                    enabled = !busy,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(64.dp)
                ) {
                    Text("Entrar a Muse", fontSize = 18.sp)
                }
                Button(
                    onClick = { send("muse --yolo") },
                    enabled = !busy,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(64.dp)
                ) {
                    Text("Entrar con YOLO", fontSize = 18.sp)
                }
                Text(
                    status,
                    color = when (lastOk) {
                        true -> Color(0xFF4CAF50)
                        false -> Color(0xFFEF5350)
                        null -> Color.Gray
                    }
                )
                Spacer(modifier = Modifier.weight(1f))
                Text(
                    "Solo funciona en este celular, no compartas tu token",
                    color = Color.Gray,
                    fontSize = 13.sp
                )
            }
        }
    }
}
