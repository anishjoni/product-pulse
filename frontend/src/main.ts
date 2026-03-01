import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
import 'primeicons/primeicons.css'

import App from './App.vue'
import { WealthsimpleTheme } from './theme/wealthsimple'

const app = createApp(App)

app.use(createPinia())
app.use(PrimeVue, {
  theme: {
    preset: WealthsimpleTheme,
    options: {
      darkModeSelector: '.dark-mode',
    },
  },
})
app.use(ToastService)

app.mount('#app')
