message("including $$PWD")

QT -= core gui

CONFIG += C++11
CONFIG += hide_symbols

TEMPLATE = lib
TARGET = shvcore

isEmpty(SHV_PROJECT_TOP_BUILDDIR) {
	SHV_PROJECT_TOP_BUILDDIR=$$shadowed($$PWD)/..
}
message ( SHV_PROJECT_TOP_BUILDDIR: '$$SHV_PROJECT_TOP_BUILDDIR' )

unix:DESTDIR = $$SHV_PROJECT_TOP_BUILDDIR/lib
win32:DESTDIR = $$SHV_PROJECT_TOP_BUILDDIR/bin

message ( DESTDIR: $$DESTDIR )

DEFINES += SHVCORE_BUILD_DLL

INCLUDEPATH += \
	#$$QUICKBOX_HOME/libqf/libqfcore/include \
	../3rdparty/necrolog/include \

LIBS += \
    -L$$DESTDIR \
    -lnecrolog
    #-lqfcore

include($$PWD/src/src.pri)
