const config = {
  title: 'Physical AI & Humanoid Robotics',
  tagline: 'AI Systems in the Physical World - Embodied Intelligence',
  favicon: 'img/favicon.ico',
  url: 'https://HamzaACCA.github.io',
  baseUrl: '/book-physical-ai-robotics/',
  organizationName: 'HamzaACCA',
  projectName: 'book-physical-ai-robotics',
  onBrokenLinks: 'ignore',
  onBrokenMarkdownLinks: 'ignore',
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },
  presets: [
    [
      'classic',
      ({
        docs: {
          sidebarPath: './sidebars.js',
          routeBasePath: '/',
        },
        blog: false,
        theme: {},
      }),
    ],
  ],
  scripts: [
    {
      src: '/book-physical-ai-robotics/chat-widget.js',
      async: true,
    },
  ],
  themeConfig: ({
    navbar: {
      title: 'Physical AI & Humanoid Robotics',
      items: [
        {
          href: 'https://github.com/HamzaACCA/book-physical-ai-robotics',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      copyright: `Physical AI & Humanoid Robotics Course - Built with Docusaurus`,
    },
    prism: {
      theme: require('prism-react-renderer').themes.github,
      darkTheme: require('prism-react-renderer').themes.dracula,
    },
  }),
};

module.exports = config;
