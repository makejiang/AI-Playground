<template>
    <div class="container">
        <h2>{{ oemName }} {{ languages.ISVAPP_TITLE }}</h2>
        <div class="disclaimer">
            * {{ languages.ISVAPP_DESCRIPTION }}
        </div>
        <div class="app-grid">
            <CardComp v-for="(app, index) in apps" :key="index" :app="app" />
        </div>
    </div>
</template>
  
<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useGlobalSetup } from '@/assets/js/store/globalSetup'
import CardComp from '@/components/CardApp.vue'
import { useI18N } from '@/assets/js/store/i18n'
import { emitter } from '@/assets/js/util.ts'
import type { App } from '@/components/CardApp.vue'

const globalSetup = useGlobalSetup()
const i18n = useI18N()
const oemName = ref<string>('OEM')

const apps = reactive<App[]>([{
    name: '',
    nameCN: '',
    tags: [],
    iconUrl: '',
    iconData: '',
    homeUrl: '',
    installer: '',
    processname: '',
    installedname: '',
}])



emitter.on('backendReady', () => {
    console.log('backendReady event received')
    refreshApps()
})

const refreshApps = async (): Promise<void> => {
    try {
        // Clear existing apps
        apps.splice(0)
        
        // Get OEM info from API
        const response = await fetch(`${globalSetup.apiHost}/api/app/getOemAppInfo`, {
            method: 'POST'
        })
        
        if (!response.ok) {
            console.error('Failed to fetch OEM info:', response.statusText)
            return
        }

        const oemAppInfo = await response.json()
        console.log('Language:', i18n.langName, i18n.currentLanguageName)
        console.log('OEM App Info:', oemAppInfo)

        // Set OEM name based on current language
        oemName.value = i18n.langName === 'zh-CN' ? oemAppInfo.name_cn : oemAppInfo.name

        for (const app of oemAppInfo.apps) {
            apps.push(app)
        }
    } catch (error) {
        console.error('Failed to refresh apps:', error)
    }
}

</script>
  
<style scoped>
    .container {
        max-width: 1500px;
        margin: 0 auto;
        padding: 20px;
        padding-top: 80px;
    }

    h2 {
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 5px;
        color: white;
    }

    .disclaimer {
        font-size: 14px;
        margin-bottom: 50px;
        color: white;
    }
    
    
  .title {
    font-size: 30px;
    font-weight: bold;
    color: #ffffff;
    margin: 0;
  }
  
  .more-link {
    color: #0088ff;
    text-decoration: none;
    font-size: 14px;
  }
  
  .app-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
  }
  
  
  @media (max-width: 992px) {
    .app-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }
  
  @media (max-width: 576px) {
    .app-grid {
      grid-template-columns: 1fr;
    }
    
    .app-tags {
      max-width: 150px;
    }
  }
</style>