<template>
  <footer class="app-footer">
    <div class="footer-content">
      <p>&copy; 2026 GitLab Insights. All rights reserved.</p>
    </div>
  </footer>
</template>

<script setup>
// Footer component
</script>

<style lang="scss" scoped>
.app-footer {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  color: #94a3b8;
  padding: 40px 0;
  text-align: center;
  border-top: 1px solid rgba(59, 130, 246, 0.1);
  
  .footer-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 40px;
    font-size: 14px;
    font-weight: 500;
  }
}
</style>
