<template>
    <div class="container">
        <h2>[OEM]精选AI应用</h2>
        <div class="disclaimer">
            *为[OEM]深度适配的软件应用程序，配合 Intel 酷睿 Ultra 处理器和 Intel Arc 显卡获取最佳使用体验。
        </div>
        <div class="app-grid">
            <CardComponent v-for="(app, index) in apps" :key="index" :app="app" />
        </div>
    </div>
  </template>
  
<script setup lang="ts">
import CardComponent from '@/components/CardApp.vue';
//import { ref, reactive } from 'vue';

const apps = reactive([
    {
        name: 'Coze',
        nameCN: '扣子',
        tags: ['工作流', 'AI', '效率', '助手'],
        iconUrl: '/oembundle/logo.coze.png',
        homeUrl: 'https://www.smfyun.com/',
        installer: 'Intel-AIPC-Agent-Setup.exe',
        processname: 'Intel-AIPC-Agent.exe',
        installedname: 'Intel-AIPC-Agent',
        uninstallProcessName: '',
    },
    {
        name: 'FlowyAI',
        nameCN: 'FlowyAIPC助手',
        tags: ['生产力', 'AI', '安全', '娱乐'],
        iconUrl: '/oembundle/logo.flowy.png',
        homeUrl: 'https://www.flowyaipc.com/',
        installer: 'Flowy AIPC-2.1.3-beta1-setup.exe',
        processname: 'Flowy AIPC.exe',
        installedname: 'Flowy AIPC',
        uninstallProcessName: 'Un_A.exe',
    },    
    {
        name: 'AIPPT',
        nameCN: 'AIPPT',
        tags: ['PPT', '办公', 'AI', '模板'],
        iconUrl: '/oembundle/logo.aippt.png',
        homeUrl: 'https://www.smfyun.com/',
        installer: 'aipc-electron-1.0.0-setup.exe',
        processname: 'AiPPT.exe',
        installedname: 'AiPPT',
        uninstallProcessName: 'Un_A.exe',
    },
    {
        name: 'SmartVision',
        nameCN: '神州问学',
        tags: ['工作流', 'AI', '业务', '低代码'],
        iconUrl: '/oembundle/logo.szwx.svg',
        homeUrl: 'https://smartvision.dcclouds.com',
        installer: '',
        processname: '',
        installedname: '',
        uninstallProcessName: '',
    },
    {
        name: 'OfficeAI',
        nameCN: 'OfficeAI助手',
        tags: ['办公', '效率', 'AI', '自动化'],
        iconUrl: '/oembundle/logo.officeai.png',
        homeUrl: 'https://www.smfyun.com/',
        installer: '',
        processname: '',
        installedname: '',
        uninstallProcessName: '',
    },
    {
        name: 'smfyun',
        nameCN: '神马',
        tags: ['搜索', 'AI', '购物', 'App Store'],
        iconUrl: '/oembundle/logo.smfyun.png',
        homeUrl: 'https://www.smfyun.com/',
        installer: '',
        processname: '',
        installedname: '',
        uninstallProcessName: '',
    },
    {
        name: 'Kutool For Excel',
        nameCN: 'Kutools For Excel',
        tags: ['Office', 'AI', '助手', '效率'],
        iconUrl: '/oembundle/logo.kutools.png',
        homeUrl: 'https://zh-cn.extendoffice.com',
        installer: 'KutoolsforExcelSetup.exe',
        processname: '',
        installedname: '',
        uninstallProcessName: '',
    },
    {
        name: 'Kutool For Word',
        nameCN: 'Kutools For Word',
        tags: ['Office', 'AI', '助手', '效率'],
        iconUrl: '/oembundle/logo.kutools.png',
        homeUrl: 'https://zh-cn.extendoffice.com',
        installer: 'WordKutools.exe',
        processname: '',
        installedname: '',
        uninstallProcessName: '',
    },
    {
        name: 'Kutool For Outlook',
        nameCN: 'Kutools For Outlook',
        tags: ['Office', 'AI', '助手', '效率'],
        iconUrl: '/oembundle/logo.kutools.png',
        homeUrl: 'https://zh-cn.extendoffice.com',
        installer: 'OutlookKutools.exe',
        processname: '',
        installedname: '',
        uninstallProcessName: '',
    },
]);

function addApp(appData: typeof apps[number]): void {
    apps.push(appData);
}

function replaceApp(index: number, newAppData: typeof apps[number]): void {
    if (index >= 0 && index < apps.length) {
        apps[index] = newAppData;
    }
}

function removeApp(index: number): void {
    if (index >= 0 && index < apps.length) {
        apps.splice(index, 1);
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