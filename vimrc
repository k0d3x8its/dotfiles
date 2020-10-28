syntax on

set rtp+=/usr/local/lib/python3.8/dist-packages/powerline/bindings/vim
set laststatus=2
set t_Co=256
set encoding=UTF-8
set guifont=DroidSansMono\ Nerd\ Font\ 11
set nu
set noswapfile
set wrap
set tabstop=4 softtabstop=4
set smartindent
set cursorline
set colorcolumn=80

highlight ColorColumn ctermbg=235
highlight CursorLine cterm=bold ctermbg=235

call plug#begin('~/.vim/plugged')

Plug 'wdhg/dragon-energy'
Plug 'preservim/nerdtree'
Plug 'ryanoasis/vim-devicons'

call plug#end()





