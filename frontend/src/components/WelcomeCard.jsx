export default function WelcomeCard() {
    return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '70vh' }}>
            <div className="welcome-card">
                <img src="/logo.png" alt="Clínica Vida" />
                <h2>Bienvenido al Sistema de Reabastecimiento</h2>
                <p>
                    Cargue sus archivos de movimientos y canastas desde la barra lateral,
                    o genere datos de prueba para explorar el sistema.
                </p>
            </div>
        </div>
    )
}
